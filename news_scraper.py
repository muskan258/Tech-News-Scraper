import requests
from bs4 import BeautifulSoup
import win32com.client
from datetime import datetime
import google.generativeai as genai
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import traceback
import random
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API and recipient email
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')

if not GOOGLE_API_KEY or not RECIPIENT_EMAIL:
    raise ValueError("Please set GOOGLE_API_KEY and RECIPIENT_EMAIL in your .env file")

genai.configure(api_key=GOOGLE_API_KEY)

# Initialize Gemini model
model = genai.GenerativeModel('gemini-pro')

# Configure requests with retry strategy
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)

# List of user agents for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59'
]

class NewsSource:
    def __init__(self, name, url, selectors, category=''):
        self.name = name
        self.url = url
        self.selectors = selectors
        self.category = category

# Define news sources with multiple possible selectors for each element
NEWS_SOURCES = [
    NewsSource(
        "TechCrunch",
        "https://techcrunch.com",
        {
            'article': ['article.post-block', 'div.post-block'],
            'title': ['h2.post-block__title', 'h2 a', 'h2'],
            'link': ['a.post-block__title__link', 'h2 a', 'a']
        },
        'Startup & Business'
    ),
    NewsSource(
        "The Verge",
        "https://www.theverge.com/tech",
        {
            'article': ['div.duet--content-cards--content-card', 'article'],
            'title': ['h2', 'h3'],
            'link': ['a']
        },
        'General Tech'
    ),
    NewsSource(
        "Ars Technica",
        "https://arstechnica.com/gadgets/",
        {
            'article': ['article', 'div.article'],
            'title': ['h2', 'header h2'],
            'link': ['a']
        },
        'In-Depth Tech'
    ),
    NewsSource(
        "TechRadar",
        "https://www.techradar.com/news/computing",
        {
            'article': ['div.article-container', 'article'],
            'title': ['h3', 'h2'],
            'link': ['a']
        },
        'Hardware & Reviews'
    ),
    NewsSource(
        "Hacker News",
        "https://news.ycombinator.com",
        {
            'article': ['tr.athing'],
            'title': ['td.title a'],
            'link': ['td.title a']
        },
        'Developer News'
    ),
    NewsSource(
        "MIT Technology Review",
        "https://www.technologyreview.com/topic/artificial-intelligence/",
        {
            'article': ['div.card--card', 'article'],
            'title': ['h3', 'h2'],
            'link': ['a']
        },
        'AI & Research'
    ),
    NewsSource(
        "The Next Web",
        "https://thenextweb.com/neural",
        {
            'article': ['article', 'div.story'],
            'title': ['h2', 'h3'],
            'link': ['a']
        },
        'AI & Future Tech'
    ),
    NewsSource(
        "VentureBeat",
        "https://venturebeat.com/ai/",
        {
            'article': ['article.Article', 'article'],
            'title': ['h2', 'h3'],
            'link': ['a']
        },
        'AI & Business'
    )
]

def find_element(soup, selectors):
    """Try multiple selectors to find an element"""
    for selector in selectors:
        try:
            if '.' in selector:
                tag, class_name = selector.split('.')
                element = soup.find(tag, class_=class_name)
            else:
                element = soup.find(selector)
            if element:
                return element
        except Exception:
            continue
    return None

def find_all_elements(soup, selectors, limit=3):
    """Try multiple selectors to find all elements"""
    for selector in selectors:
        try:
            if '.' in selector:
                tag, class_name = selector.split('.')
                elements = soup.find_all(tag, class_=class_name, limit=limit)
            else:
                elements = soup.find_all(selector, limit=limit)
            if elements:
                return elements
        except Exception:
            continue
    return []

def clean_text(text):
    """Clean and format text"""
    if not text:
        return ""
    # Remove extra whitespace and newlines
    text = ' '.join(text.split())
    # Truncate if too long
    return text[:200] + '...' if len(text) > 200 else text

def generate_summary(title, content, source):
    """Generate a short summary using Gemini AI"""
    try:
        prompt = f"""
        Generate a 1-2 sentence summary of this tech news article.
        Title: {title}
        Content: {content}
        Source: {source}
        
        Make the summary engaging and highlight the key points. Focus on the impact and significance.
        Keep it under 150 characters.
        """
        
        response = model.generate_content(prompt)
        summary = response.text.strip()
        return summary[:150] + '...' if len(summary) > 150 else summary
    except Exception as e:
        print(f"Error generating summary: {str(e)}")
        return content[:150] + '...' if content else "No summary available."

def scrape_news(source):
    """Scrape latest news from a given source"""
    try:
        print(f"\nAttempting to scrape {source.name}...")
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        # Add random delay between requests
        time.sleep(random.uniform(1, 3))
        
        response = http.get(source.url, headers=headers, timeout=15)
        response.raise_for_status()
        print(f"Successfully fetched {source.name} homepage")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []
        
        # Find all article elements
        article_elements = find_all_elements(soup, source.selectors['article'])
        print(f"Found {len(article_elements)} potential articles on {source.name}")
        
        for article in article_elements:
            try:
                # Find title element
                title_element = None
                for selector in source.selectors['title']:
                    title_element = find_element(article, [selector])
                    if title_element:
                        break
                
                if not title_element:
                    continue
                
                title = clean_text(title_element.text)
                
                # Find link element
                link = None
                for selector in source.selectors['link']:
                    link_element = find_element(article, [selector])
                    if link_element and link_element.get('href'):
                        link = link_element['href']
                        break
                
                if not link:
                    continue
                
                # Handle relative URLs
                if link.startswith('//'):
                    link = 'https:' + link
                elif link.startswith('/'):
                    link = source.url.split('/')[0] + '//' + source.url.split('/')[2] + link
                elif not link.startswith('http'):
                    link = source.url.rstrip('/') + '/' + link.lstrip('/')
                
                # Get article summary
                summary = ""
                try:
                    if link:
                        article_response = http.get(link, headers=headers, timeout=10)
                        article_soup = BeautifulSoup(article_response.text, 'html.parser')
                        
                        # Try meta description first
                        meta_desc = article_soup.find('meta', {'name': ['description', 'og:description', 'twitter:description']})
                        if meta_desc:
                            summary = meta_desc.get('content', '')
                        
                        # If no meta description, try first paragraph
                        if not summary:
                            first_p = article_soup.find('p')
                            if first_p:
                                summary = first_p.text.strip()
                        
                        # Generate AI summary
                        ai_summary = generate_summary(title, summary, source.name)
                        
                except Exception as e:
                    print(f"Error getting summary for {link}: {str(e)}")
                    ai_summary = "Summary not available"
                
                articles.append({
                    'title': title,
                    'link': link,
                    'source': source.name,
                    'summary': summary,
                    'ai_summary': ai_summary,
                    'category': source.category
                })
                print(f"Successfully processed article: {title[:50]}...")
                
            except Exception as e:
                print(f"Error processing article from {source.name}: {str(e)}")
                continue
        
        return articles
    except Exception as e:
        print(f"Error scraping {source.name}: {str(e)}")
        print("Traceback:", traceback.format_exc())
        return []

def send_email(news_items):
    """Send email using local Outlook client"""
    try:
        outlook = win32com.client.Dispatch('Outlook.Application')
        mail = outlook.CreateItem(0)
        
        mail.To = RECIPIENT_EMAIL
        mail.Subject = f'Tech News Summary - {datetime.now().strftime("%Y-%m-%d %H:%M")}'
        
        # Create HTML body with improved styling
        body = """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
        <div style="background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <h1 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; text-align: center;">
                🌐 Today's Tech News Roundup
            </h1>
            <p style="color: #666; text-align: center;">
                Curated tech news with AI-powered summaries
            </p>
        """
        
        # Group articles by category
        news_by_category = {}
        for item in news_items:
            category = item.get('category', 'General')
            if category not in news_by_category:
                news_by_category[category] = []
            news_by_category[category].append(item)
        
        # Sort categories
        for category in sorted(news_by_category.keys()):
            body += f'''
            <div style="margin-top: 30px;">
                <h2 style="color: #2c3e50; background-color: #f8f9fa; padding: 10px; border-radius: 5px;">
                    📌 {category}
                </h2>
            '''
            
            for item in news_by_category[category]:
                body += f"""
                <div style="margin: 20px 0; padding: 15px; border-left: 4px solid #3498db; background-color: #f8f9fa; border-radius: 5px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h3 style="margin: 0; flex: 1;">
                            <a href="{item['link']}" style="color: #3498db; text-decoration: none; hover: underline;">
                                {item['title']}
                            </a>
                        </h3>
                        <span style="color: #666; font-size: 0.9em; margin-left: 10px;">
                            {item['source']}
                        </span>
                    </div>
                    <div style="margin-top: 10px; padding: 10px; background-color: #fff; border-radius: 5px;">
                        <p style="color: #2c3e50; margin: 0; font-weight: bold;">🤖 AI Summary:</p>
                        <p style="color: #666; margin: 5px 0 0 0; line-height: 1.4;">
                            {item.get('ai_summary', 'No summary available.')}
                        </p>
                    </div>
                    <p style="color: #666; margin-top: 10px; line-height: 1.6;">
                        {item.get('summary', '')}
                    </p>
                </div>
                """
            body += "</div>"
        
        body += f"""
        <div style="margin-top: 30px; border-top: 1px solid #ddd; padding-top: 20px; text-align: center; color: #666;">
            <p>Generated by Tech News Scraper on {datetime.now().strftime("%Y-%m-%d at %H:%M")}</p>
            <p style="font-size: 0.9em;">To unsubscribe, reply to this email with "unsubscribe" in the subject.</p>
        </div>
        </div>
        </body>
        </html>
        """
        
        mail.HTMLBody = body
        mail.Send()
        print("\nEmail sent successfully via Outlook!")
    except Exception as e:
        print(f"\nError sending email: {str(e)}")
        print("Traceback:", traceback.format_exc())

def main():
    print("Starting news scraping...")
    all_news = []
    
    for source in NEWS_SOURCES:
        news_items = scrape_news(source)
        if news_items:
            print(f"Found {len(news_items)} articles from {source.name}")
            all_news.extend(news_items)
        time.sleep(2)  # Be nice to the servers
    
    if all_news:
        print(f"\nFound total of {len(all_news)} news items. Sending email...")
        send_email(all_news)
    else:
        print("\nNo news items found. Please check the website selectors or try again later.")

if __name__ == "__main__":
    main()
