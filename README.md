# Tech News Scraper

A Python script that scrapes daily tech news from trusted sources and sends a beautifully formatted email digest with AI-powered summaries.

## Features

- 🔍 Scrapes news from multiple trusted tech sources:
  - TechCrunch (Startup & Business)
  - The Verge (General Tech)
  - Ars Technica (In-Depth Tech)
  - TechRadar (Hardware & Reviews)
  - Hacker News (Developer News)
  - MIT Technology Review (AI & Research)
  - The Next Web (AI & Future Tech)
  - VentureBeat (AI & Business)

- 🤖 AI-Powered Features:
  - Concise summaries generated using Google's Gemini AI
  - Smart categorization of articles
  - Focused on impact and significance

- 📧 Email Features:
  - Beautiful HTML formatting
  - Articles grouped by category
  - Both AI summary and original description
  - Clean, modern design
  - Unsubscribe option

- 🛡️ Robust Error Handling:
  - Automatic retries for failed requests
  - Multiple selector fallbacks
  - Comprehensive error logging
  - Random delays and user agent rotation

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your configuration:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key
   RECIPIENT_EMAIL=your_email@example.com
   ```

4. Make sure you have Outlook installed and configured on your system

## Usage

Run the script manually:
```bash
python news_scraper.py
```

Or set up a scheduled task to run it daily:
1. Open Task Scheduler
2. Create a new task
3. Set the trigger to run daily at your preferred time
4. Action: Start a program
   - Program/script: python
   - Arguments: news_scraper.py
   - Start in: [path_to_script_directory]

## Requirements

- Python 3.8+
- Microsoft Outlook (installed and configured)
- Google Gemini API key
- Active internet connection

## Dependencies

- requests: HTTP requests with retry support
- beautifulsoup4: HTML parsing
- pywin32: Outlook integration
- google-generativeai: AI summaries
- python-dotenv: Environment variable management

## Error Handling

The script includes comprehensive error handling:
- Retries failed HTTP requests
- Gracefully handles parsing errors
- Continues processing if one source fails
- Logs all errors for debugging

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
