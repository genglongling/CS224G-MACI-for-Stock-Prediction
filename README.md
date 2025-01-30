# 🚀 CS224G-MACI-for-Stock-Prediction  

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
- 🚀 **(Sprint 2)** First App Demo →  
- 🔧 **(Sprint 3)** Enhancement, Second App Demo →  
- 🎤 **(Demo Day)** Paper Submission for NeurIPS, Final App Demo →  

### 🤖 3.4 Multi-Agent App Development:  

- 🔍 **(1) LLM Specialization**: Different LLMs tailored for **Stock Prediction, Company Analysis, Personal Insights, and Job Market Trends**.  
- 🏗 **(2) Overall Architecture**: Multi-Agents selection and collaboration, to generate holistic financial and career insights.  
- 📈 **(3) Agent 1 & 2: Stock Prediction & Company Analysis**: Real-time data integration, LLMs for market trends and company analysis.  
- 👥 **(4) Agent 3 & 4: Investment Expert Analysis & Job Analysis**: AI-driven investment, career suggestion, and matching based on market shifts.  
- 🚀 **(5) Milestones**: Iterative development, testing, and user feedback loops.
  
---

## ⚙️ 4. Experiment Set-up  

We plan to evaluate our multi-agent temporal planning framework on **S&P 500 stocks (2018-2024)**, incorporating historical trading data, reports data, and other relevant financial data. Our focus will be on three major market sectors.  

All experiments will utilize publicly available data from sources like:  

- 📈 **Yahoo Finance** (Stock Prices)  
- 📜 **SEC EDGAR** (Financial Reports)  

### ⚖️ 4.1 Baselines & Comparisons:  

1. 📊 **Baseline Models:**  
   - Traditional machine learning methods (**Logistic Regression, SVM, LSTM networks**).  

2. 🆚 **Comparison with MACI:**  
   - Evaluating prediction accuracy (**MAE, MSE**) and **directional accuracy** for stock movement prediction.  

3. 🧩 **Ablation Studies:**  
   - Testing different combinations of agents and their impact on performance.  

4. 📊 **Robustness & Scalability:**  
   - Assessing performance across different market conditions and unseen stocks (out-of-sample validation).  

---

## 🎓 5. Contribution  

1. 📄 **Paper: Multi-Agent Collaborative Intelligence for Robust Temporal Planning** – *Edward Y. Chang*  
2. 📄 **Paper: Multi-Agent Collaborative Intelligence Application: Stock Prediction Case** – *Longling Gloria Geng, Arihant Choudhary, Parth Behani, Edward Y. Chang*  
3. 💻 **GitHub Setup and Experiments** – *Longling Gloria Geng*  

---
# 🚀 How to Run the Code

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

This **README** provides an overview of the **CS224G MACI for Stock Prediction** project, highlighting its **motivations, project plan, methodologies, demo, and future directions.** 🚀  
