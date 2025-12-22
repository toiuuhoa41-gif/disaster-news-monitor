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

    console.log('📊 Fetching dashboard statistics...');

    // Get total articles count
    const { count: totalArticles } = await supabase
      .from('articles')
      .select('*', { count: 'exact', head: true });

    // Get disaster articles (high + medium severity)
    const { count: disasterArticles } = await supabase
      .from('articles')
      .select('*', { count: 'exact', head: true })
      .in('severity', ['high', 'medium']);

    // Get today's articles
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const { count: todayArticles } = await supabase
      .from('articles')
      .select('*', { count: 'exact', head: true })
      .gte('created_at', today.toISOString());

    // Get active sources
    const { count: activeSources } = await supabase
      .from('sources')
      .select('*', { count: 'exact', head: true })
      .eq('status', 'active');

    // Get sources list
    const { data: sources } = await supabase
      .from('sources')
      .select('*')
      .order('articles_count', { ascending: false });

    // Get latest crawl log
    const { data: latestCrawl } = await supabase
      .from('crawl_logs')
      .select('*')
      .order('started_at', { ascending: false })
      .limit(1)
      .maybeSingle();

    // Get severity distribution
    const { data: severityData } = await supabase
      .from('articles')
      .select('severity');

    const severityDistribution = {
      high: 0,
      medium: 0,
      low: 0,
    };

    severityData?.forEach((article) => {
      if (article.severity && severityDistribution[article.severity as keyof typeof severityDistribution] !== undefined) {
        severityDistribution[article.severity as keyof typeof severityDistribution]++;
      }
    });

    // Get category distribution
    const { data: categoryData } = await supabase
      .from('articles')
      .select('category');

    const categoryCount: Record<string, number> = {};
    categoryData?.forEach((article) => {
      const cat = article.category || 'Khác';
      categoryCount[cat] = (categoryCount[cat] || 0) + 1;
    });

    const categoryDistribution = Object.entries(categoryCount)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 5);

    console.log(`✅ Stats: ${totalArticles} total, ${disasterArticles} disaster, ${todayArticles} today`);

    return new Response(
      JSON.stringify({
        success: true,
        data: {
          totalArticles: totalArticles || 0,
          disasterArticles: disasterArticles || 0,
          todayArticles: todayArticles || 0,
          activeSources: activeSources || 0,
          sources: sources || [],
          latestCrawl,
          severityDistribution,
          categoryDistribution,
          lastUpdate: new Date().toISOString(),
        },
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    console.error('❌ Error in get-stats function:', error);
    return new Response(
      JSON.stringify({ error: errorMessage, success: false }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});
