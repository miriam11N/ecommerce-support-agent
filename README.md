E-commerce Support Assistant



A portfolio project that answers questions about synthetic e-commerce orders. It retrieves order and payment information from SQLite and related product reviews from MongoDB Atlas. Claude Haiku drafts a response, and the app uses a safer preset response if the draft fails its checks or Claude is unavailable.



Features



\- Chat website and FastAPI backend

\- SQLite order lookup and MongoDB product-review retrieval

\- Claude-assisted replies with a preset fallback

\- Jupyter notebook with four charts showing order value, products, review ratings, and ticket categories



How to run locally



1\. Create and activate a Python virtual environment.

2\. Install dependencies with `pip install -r requirements.txt`.

3\. Create a `.env` file containing `MONGODB\_URI` and `ANTHROPIC\_API\_KEY`. Do not upload this file to GitHub.

4\. For a fresh setup, run `python seed\_sqlite.py` and then `python seed\_mongo.py`.

5\. Start the app with `python -m uvicorn app:app --reload`.

6\. Open `http://127.0.0.1:8000/` in your browser.



Example questions



\- “I want to return order 1001.”

\- “Where is order 1002?”



Limitations



The data is synthetic. The app cannot approve returns, issue refunds, or provide tracking information. Reviews are retrieved by product ID, not by semantic search. Claude writes drafts but does not independently choose or call database tools. This is a portfolio demonstration, not a production customer-support system.

