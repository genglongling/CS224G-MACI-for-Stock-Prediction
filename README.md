# 🚀 CS224G-MACI-for-Stock-Prediction  

## [Sprint 4 - NEW UPDATE]
## - Please review section How To Run The Code Part D for the app
## - Code: cd MACI_stock_prediction
## [Sprint 3 - UPDATE]
## - Paper: [MACI Framework](https://arxiv.org/abs/2502.18836)
## - Code: cd MACI_framework


# 🏗️ **7 Multi-Agent tools**  
   - Our newest version MACI support Magentic multi-agent tool.
   - Our previous MACI-framework could support multi-agent tools: LangGraph, AutoGen, Crewai, LangChain, and to be extended on LlamaIndex, Haystack.

# 🤝 **20+ LLM Agents**  
   - **[OpenAI LLMs:](https://openai.com/)** including gpt-4, gpt-4o, gpt-4o-mini, etc.
   - **[Ollama:](https://ollama.com/)** including Llama 3.3, DeepSeek-R1, Phi-4, Mistral, Gemma 2, etc.
   - **[Anthropic:](https://www.anthropic.com/)** including Claud 3.7.
   - **[Mistral:](https://mistral.ai/)** 
   - **[LiteLLM:](https://docs.litellm.ai/)** 
   - **or any other OpenAI schema-compatible model** 
   - **FinAgent(ours)**
   - **Your Self-developed LLMs(ours)**
   - **Access to financial database such as [Alphavantage](https://www.alphavantage.co/documentation/), and yahoo api.** adapts to unexpected changes in real-time financial information.

# 🤖 **Interactive Back-End App**  
## ⚠️ 1. LLM Limitations in Complex Planning  

Large Language Models (LLMs) excel at pattern recognition but struggle with complex planning tasks that require:  

- 🧠 **Deliberate reasoning**  
- ⏳ **Temporal awareness**  
- 📏 **Constraint management**  

### 🔍 1.1 Key Limitations of Current LLM Models:  

1. ❌ **Lack of Self-Verification**  
   - LLMs cannot validate their own outputs, leading to errors.  

2. 🎯 **Attention Bias & Constraint Drift**  
   - Contextual focus shifts, ignoring earlier constraints.  

3. 🏗️ **Lack of Common Sense Integration**  
   - Omits real-world constraints (e.g., logistics delays).  

---

## 🤖 2. MACI: Multi-Agent Collaborative Intelligence  

MACI is designed to overcome these LLM limitations using a three-layer approach:  

1. 🏗️ **Meta-Planner (MP)**  
   - Constructs task-specific workflows, identifying roles and constraints.  

2. 🤝 **Common & Task-Specific Agents**  
   - **Common Agents:** Validate constraints & reasoning quality.  
   - **Task-Specific Agents:** Optimize domain-specific tasks.  

3. 📡 **Run-Time Monitor**  
   - Adapts to unexpected changes in real-time.  

---

## 📅 3. Project Plan  

### 🔄 3.1 LLM Model Improvement on:  

1. ✅ **Lack of Self-Verification**  
   - Independent validation agents ensure correctness.  

2. 🔍 **Attention Bias**  
   - Task-specific agents with constrained context windows prevent bias.  

3. 🌍 **Lack of Common Sense**  
   - Integration agents enhance real-world feasibility.  

### 🧪 3.2 LLM Research and Experiments:  

- 📝 Spec completed, paper submitted to ICML.  
- 🏆 Tested on **Traveling Salesperson** & **Thanksgiving Dinner Planning**, outperforming all LLMs, including DeepSeek.  
- 📊 Stock Prediction application designed.  

### 📆 3.3 General Timeline:  

- 🏗 **(Sprint 1)** Implementation, Experiments, First Results →  
- 🚀 **(Sprint 2)** First App Demo (Frond-End & Back-End) →  
- 🔧 **(Sprint 3)** MACI Enhancement, Second App Demo →  
- 🎤 **(Demo Day)** App Integration, Paper Submission for NeurIPS, Final App Demo →  

### 🤖 3.4 Multi-Agent App Development:  

- 🔍 **(1) LLM Specializatio✅**: Different LLMs tailored for **Stock Prediction, Company Analysis, Personal Insights, and Job Market Trends**.  
- 🏗 **(2) Overall Architecture✅**: Using **MACI Framework with website**, Multi-Agents selection and collaboration, to generate holistic financial and career insights.  
- 📈 **(3) Agent 1 & 2✅: Stock Prediction & Company Analysis**: Real-time data integration, LLMs for market trends and company analysis.  
- 👥 **(4) Agent 3 & 4✅: Investment Expert Analysis & Job Analysis**: AI-driven investment, career suggestion, and matching based on market shifts.  
- 🚀 **(5) Milestones**: Iterative development, testing, and user feedback loops.
  
---

## ⚙️ 4. Experiment Set-up  

We plan to evaluate our multi-agent temporal planning framework on **S&P 500 stocks (2018-2024)**, incorporating historical trading data, reports data, and other relevant financial data. Our focus will be on three major market sectors.  

All experiments will utilize publicly available data from sources like:  

- 📈 **Yahoo Finance** (Stock Prices)  
- 📜 **SEC EDGAR** (Financial Reports)  

### ⚖️ 4.1 Baselines & Comparisons:  

1. 📊 **Baseline Models:**  
   - Traditional machine learning methods (**Logistic Regression, SVM, LSTM(best), LLM, MACI(best) networks**).  

2. 🆚 **Comparison with MACI:**  
   - Evaluating prediction accuracy (**MAE, MSE**) and **directional accuracy** for stock movement prediction.  

3. 🧩 **Ablation Studies:**  
   - Testing different combinations of agents and their impact on performance.  

4. 📊 **Robustness & Scalability:**  
   - Assessing performance across different market conditions and unseen stocks (out-of-sample validation).  

---

## 🎓 5. Contribution  

1. 📄 **Paper: Multi-Agent Collaborative Intelligence for Robust Temporal Planning** – *Edward Y. Chang*  
2. 📄 **Paper: REALM-Bench: A Real-World Planning Benchmark for LLMs and Multi-Agent Systems** – *Longling Gloria Geng, Edward Y. Chang*  
3. 💻 **GitHub Setup, App Development, and Experiments** – *Longling Gloria Geng*  

---
# 🚀 How to Run the Code

## A. Base Experiments
## 1) (Optional) Create and Activate a Virtual Environment
It is recommended to use a virtual environment to manage dependencies:

```sh
python3 -m venv env
source env/bin/activate  # On macOS/Linux
env\Scripts\activate     # On Windows
```

## 2) Install Dependencies
Ensure you have all necessary dependencies installed:

```sh
pip install -r requirements.txt
```

Or install manually:

```sh
pip install pandas numpy matplotlib prophet
```

## 3) Download & Place the S&P 500 Stocks Data
The dataset is available on Kaggle:  
🔗 [S&P 500 Stocks Dataset](https://www.kaggle.com/datasets/andrewmvd/sp-500-stocks)

Extract and place the CSV file inside the `sp500_stocks/` directory:

```sh
mkdir -p sp500_stocks
mv path/to/sp500_stocks.csv sp500_stocks/
```

## 4) Execute the Python Script
Run the stock prediction script:

```sh
python3 main.py
```

## 5) Wait for the Script to Finish
The script will:  
✅ Predict stock prices for **2 years into the future**  
✅ Load and preprocess the stock data  
✅ Train a **Prophet forecasting model**  
✅ Generate & save plots showing historical vs. forecasted values

## 6) View Generated Plots
Once the script completes, you’ll find the forecasted plots in the project folder:  
- `AAPL_forecast.png` → Forecast for **Apple**  
- `TSLA_forecast.png` → Forecast for **Tesla**  
- `META_forecast.png` → Forecast for **Meta**
- other plots etc.

## B. Front-End Demo
```sh
cd checkco
```
then open index.html

## C. Back-End Demo
```sh
cd checkco
python3 server.py
```
then open front.html

## D. MACI for Stock Prediction Demo (final)
```sh
cd MACI_stock_prediction
```
then follow README file to set up your own multi-agent framework and pipeline.

✅ Step 1: Run FastAPI with Uvicorn
Make sure you're in the same directory as main.py and then run:
```sh
export OPENAI_API_KEY=
export...
uvicorn main:app --reload
```

✅ Step 2: 
go to 127.0.0.1.8000/static/front.html

Check File Structure
Your project should be organized like this:
```sh
MACI-Stock-Prediction/
│── main.py  # ✅ FastAPI app entry point
│── static/  # ✅ HTML, CSS, and JavaScript for UI
│   ├── index.html
│   ├── style.css
│   ├── script.js
│── templates/  # (Optional) Jinja2 templates
│── utils/  # ✅ Helper functions (e.g., API calls)
│   ├── indicators.py
│   ├── charts.py
│── .env  # ✅ API Keys
│── requirements.txt  # ✅ Python dependencies
│── README.md  # ✅ Project documentation
```
This **README** provides an overview of the **CS224G MACI for Stock Prediction** project, highlighting its **motivations, project plan, methodologies, demo, and future directions.** 🚀  
