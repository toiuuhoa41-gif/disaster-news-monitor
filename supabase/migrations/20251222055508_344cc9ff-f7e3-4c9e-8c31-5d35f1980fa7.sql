-- Create sources table to track news sources
CREATE TABLE public.sources (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  domain TEXT NOT NULL UNIQUE,
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'warning', 'error')),
  articles_count INTEGER DEFAULT 0,
  last_crawl TIMESTAMP WITH TIME ZONE,
  categories TEXT[] DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create articles table to store crawled news
CREATE TABLE public.articles (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  url TEXT NOT NULL UNIQUE,
  source TEXT NOT NULL,
  category TEXT,
  title TEXT NOT NULL,
  authors TEXT[] DEFAULT '{}',
  publish_date TIMESTAMP WITH TIME ZONE,
  update_date TIMESTAMP WITH TIME ZONE,
  tags TEXT[] DEFAULT '{}',
  text TEXT,
  summary TEXT,
  keywords TEXT[] DEFAULT '{}',
  top_image TEXT,
  severity TEXT DEFAULT 'medium' CHECK (severity IN ('high', 'medium', 'low')),
  language TEXT DEFAULT 'vi',
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create crawl_logs table to track crawl history
CREATE TABLE public.crawl_logs (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  total_articles INTEGER DEFAULT 0,
  disaster_articles INTEGER DEFAULT 0,
  sources_crawled INTEGER DEFAULT 0,
  started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  completed_at TIMESTAMP WITH TIME ZONE,
  status TEXT DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed')),
  error_message TEXT
);

-- Enable Row Level Security
ALTER TABLE public.sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.crawl_logs ENABLE ROW LEVEL SECURITY;

-- Create public read policies (data is public for monitoring dashboard)
CREATE POLICY "Anyone can read sources" ON public.sources FOR SELECT USING (true);
CREATE POLICY "Anyone can read articles" ON public.articles FOR SELECT USING (true);
CREATE POLICY "Anyone can read crawl_logs" ON public.crawl_logs FOR SELECT USING (true);

-- Create indexes for better query performance
CREATE INDEX idx_articles_source ON public.articles(source);
CREATE INDEX idx_articles_publish_date ON public.articles(publish_date DESC);
CREATE INDEX idx_articles_severity ON public.articles(severity);
CREATE INDEX idx_articles_created_at ON public.articles(created_at DESC);
CREATE INDEX idx_crawl_logs_started_at ON public.crawl_logs(started_at DESC);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = public;

-- Create trigger for sources table
CREATE TRIGGER update_sources_updated_at
  BEFORE UPDATE ON public.sources
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

-- Enable realtime for articles table
ALTER PUBLICATION supabase_realtime ADD TABLE public.articles;