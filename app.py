from flask import Flask, request, jsonify
from phi.agent import Agent
from phi.model.openai import OpenAIChat
from phi.tools.yfinance import YFinanceTools

app = Flask(__name__)

# Create a finance agent
finance_agent = Agent(
    name="Finance Agent",
    model=OpenAIChat(id="gpt-4o"),
    tools=[YFinanceTools(stock_price=True, analyst_recommendations=True, company_info=True)],
    instructions=["Use tables to display data"],
)

def call_gemini_api(prompt, gemini_api_key):
    # Replace with actual Gemini API call
    # This is a placeholder for the actual API call
    return f"Summarized news for: {prompt}"

@app.route('/api/company-details/<symbol>', methods=['GET'])
def get_company_details(symbol):
    response = finance_agent.print_response(f"Get stock data for {symbol}", stream=False)
    return jsonify(response)

@app.route('/api/latest-news/<company_name>', methods=['GET'])
def get_latest_news(company_name):
    gemini_api_key = "YOUR_GEMINI_API_KEY"  # Replace with your actual Gemini API key
    prompt = f"Provide the latest news and summarize it for {company_name}."
    news_summary = call_gemini_api(prompt, gemini_api_key)
    return jsonify({"news": news_summary})

@app.route('/api/analyze/<company_name>/<symbol>', methods=['GET'])
def analyze_stock(company_name, symbol):
    stock_data = finance_agent.print_response(f"Get stock data for {symbol}", stream=False)
    news_summary = call_gemini_api(f"Provide the latest news and summarize it for {company_name}.", "YOUR_GEMINI_API_KEY")
    analysis = {
        "stock_data": stock_data,
        "latest_news": news_summary
    }
    return jsonify(analysis)

if __name__ == '__main__':
    app.run(debug=True)
