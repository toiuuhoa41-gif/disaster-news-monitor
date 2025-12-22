import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface Article {
  url: string;
  source: string;
  category?: string;
  title: string;
  authors?: string[];
  publish_date?: string;
  update_date?: string;
  tags?: string[];
  text?: string;
  summary?: string;
  keywords?: string[];
  media?: {
    top_image?: string;
    images?: string[];
    videos?: string[];
  };
  language?: string;
  severity?: 'high' | 'medium' | 'low';
}

interface IngestPayload {
  articles: Article[];
  source_id?: string;
  crawl_id?: string;
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    const payload: IngestPayload = await req.json();
    const { articles, source_id, crawl_id } = payload;

    console.log(`📥 Received ${articles.length} articles to ingest`);

    if (!articles || !Array.isArray(articles) || articles.length === 0) {
      return new Response(
        JSON.stringify({ error: 'No articles provided', success: false }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // Transform articles to match database schema
    const transformedArticles = articles.map((article) => ({
      url: article.url,
      source: article.source || source_id || 'unknown',
      category: article.category || null,
      title: article.title,
      authors: article.authors || [],
      publish_date: article.publish_date || null,
      update_date: article.update_date || null,
      tags: article.tags || [],
      text: article.text || null,
      summary: article.summary || null,
      keywords: article.keywords || [],
      top_image: article.media?.top_image || null,
      severity: article.severity || 'medium',
      language: article.language || 'vi',
    }));

    // Upsert articles (insert or update on conflict)
    const { data: insertedArticles, error: insertError } = await supabase
      .from('articles')
      .upsert(transformedArticles, { 
        onConflict: 'url',
        ignoreDuplicates: false 
      })
      .select('id, url');

    if (insertError) {
      console.error('❌ Error inserting articles:', insertError);
      return new Response(
        JSON.stringify({ error: insertError.message, success: false }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    console.log(`✅ Successfully ingested ${insertedArticles?.length || 0} articles`);

    // Update source stats if source_id provided
    if (source_id) {
      const { error: sourceError } = await supabase
        .from('sources')
        .upsert({
          id: source_id,
          name: source_id,
          domain: articles[0]?.source || source_id,
          status: 'active',
          articles_count: articles.length,
          last_crawl: new Date().toISOString(),
        }, { onConflict: 'id' });

      if (sourceError) {
        console.error('⚠️ Error updating source:', sourceError);
      }
    }

    // Update crawl log if crawl_id provided
    if (crawl_id) {
      const { error: crawlError } = await supabase
        .from('crawl_logs')
        .update({
          total_articles: articles.length,
          disaster_articles: articles.filter(a => a.severity === 'high' || a.severity === 'medium').length,
          completed_at: new Date().toISOString(),
          status: 'completed',
        })
        .eq('id', crawl_id);

      if (crawlError) {
        console.error('⚠️ Error updating crawl log:', crawlError);
      }
    }

    return new Response(
      JSON.stringify({
        success: true,
        inserted: insertedArticles?.length || 0,
        message: `Successfully ingested ${insertedArticles?.length || 0} articles`,
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    console.error('❌ Error in ingest-articles function:', error);
    return new Response(
      JSON.stringify({ error: errorMessage, success: false }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});
