# CS224G-MACI-for-Stock-Prediction

## LLM Limitations:

In Complex Planning, Large Language Models (LLMs) excel at pattern recognition but struggle with complex planning tasks that require:

- **Deliberate reasoning**  
- **Temporal awareness**  
- **Constraint management**  

### Key Limitations of current LLM models:

1. **Lack of Self-Verification**  
   - LLMs cannot validate their own outputs, leading to errors.  

2. **Attention Bias & Constraint Drift**  
   - Contextual focus shifts, ignoring earlier constraints.  

3. **Lack of Common Sense Integration**  
   - Omits real-world constraints (e.g., logistics delays).  

---

## MACI: Multi-Agent Collaborative Intelligence

MACI is designed to overcome these LLM limitations using a three-layer approach:

1. **Meta-Planner (MP)**  
   - Constructs task-specific workflows, identifying roles and constraints.  

2. **Common & Task-Specific Agents**  
   - **Common Agents:** Validate constraints & reasoning quality.  
   - **Task-Specific Agents:** Optimize domain-specific tasks.  

3. **Run-Time Monitor**  
   - Adapts to unexpected changes in real-time.  

---

## Project Plan  

### LLM Model Improvement on:

1. **Lack of Self-Verification**  
   - Independent validation agents ensure correctness.  

2. **Attention Bias**  
   - Task-specific agents with constrained context windows prevent bias.  

3. **Lack of Common Sense**  
   - Integration agents enhance real-world feasibility.  

### LLM Research and Experiments:  

- Spec completed, paper submitted to ICML.  
- Tested on **Traveling Salesperson** & **Thanksgiving Dinner Planning**, outperforming all LLMs, including DeepSeek.  
- Stock Prediction application designed.  

### General Timeline:  

- **(Sprint 1) Implementation, Experiments, First Results →**
- **(Sprint 2) First App Demo →**
- **(Sprint 3) Enhancement, Second App Demo →**
- **(Demo Day) Paper Submission for Neurips, Final App Demo →**

---

## Experiment Set-up

We plan to evaluate our multi-agent temporal planning framework on **S&P 500 stocks (2018-2024)**, incorporating historical trading data, reports data, and other relevant financial data. Our focus will be on three major market sectors.  

All experiments will utilize publicly available data from sources like:  

- **Yahoo Finance** (Stock Prices)  
- **SEC EDGAR** (Financial Reports)  

### Baselines & Comparisons:  

1. **Baseline Models:**  
   - Traditional machine learning methods (Logistic Regression, SVM, LSTM networks).  

2. **Comparison with MACI:**  
   - Evaluating prediction accuracy (**MAE, MSE**) and **directional accuracy** for stock movement prediction.  

3. **Ablation Studies:**  
   - Testing different combinations of agents and their impact on performance.  

4. **Robustness & Scalability:**  
   - Assessing performance across different market conditions and unseen stocks (out-of-sample validation).  

---

## Contribution  

1. **Paper: Multi-Agent Collaborative Intelligence for Robust Temporal Planning** – *Edward Y. Chang*  
2. **Paper: Multi-Agent Collaborative Intelligence Application: Stock Prediction Case** – *Longling Gloria Geng, Arihant Choudhary, Parth Behani, Edward Y. Chang*
3. **Github Setup and Experiments** – *Longling Gloria Geng*

---

This README provides an overview of the **CS224G MACI for Stock Prediction** project, highlighting its motivations, project plan, methodologies, demo, and future directions. 🚀
