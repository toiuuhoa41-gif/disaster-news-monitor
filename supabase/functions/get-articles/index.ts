import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_PUBLISHABLE_KEY')!;
    
    const supabase = createClient(supabaseUrl, supabaseKey);

    const url = new URL(req.url);
    const limit = parseInt(url.searchParams.get('limit') || '50');
    const offset = parseInt(url.searchParams.get('offset') || '0');
    const source = url.searchParams.get('source');
    const severity = url.searchParams.get('severity');
    const category = url.searchParams.get('category');

    console.log(`📖 Fetching articles: limit=${limit}, offset=${offset}, source=${source}, severity=${severity}`);

    let query = supabase
      .from('articles')
      .select('*', { count: 'exact' })
      .order('publish_date', { ascending: false, nullsFirst: false })
      .range(offset, offset + limit - 1);

    // Apply filters
    if (source) {
      query = query.ilike('source', `%${source}%`);
    }
    if (severity) {
      query = query.eq('severity', severity);
    }
    if (category) {
      query = query.ilike('category', `%${category}%`);
    }

    const { data: articles, error, count } = await query;

    if (error) {
      console.error('❌ Error fetching articles:', error);
      return new Response(
        JSON.stringify({ error: error.message, success: false }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    console.log(`✅ Fetched ${articles?.length || 0} articles (total: ${count})`);

    return new Response(
      JSON.stringify({
        success: true,
        data: articles,
        total: count,
        limit,
        offset,
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    console.error('❌ Error in get-articles function:', error);
    return new Response(
      JSON.stringify({ error: errorMessage, success: false }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});
