# Personal Finance Advisor

An intelligent financial analysis system that processes bank statements to provide automated spending insights and categorization.

## Overview

Personal Finance Advisor uses a hybrid multi-agent architecture to analyze monthly bank statements, automatically categorize transactions, and generate comprehensive spending reports. The system combines deterministic processing for obvious transactions with AI-powered analysis for ambiguous cases, ensuring both accuracy and cost efficiency.

## Architecture

- **Document Processor**: Extracts and parses transaction data from PDF statements using pattern recognition
- **Content Analyzer**: Intelligently categorizes unclear transactions using Claude AI
- **Analysis Generator**: Creates detailed spending reports, visualizations, and personalized insights

## Tech Stack

- **Python 3.8+** - Core development
- **Anthropic Claude** - AI-powered transaction categorization  
- **pdfplumber** - PDF document processing
- **python-dotenv** - Environment configuration
- **requests** - HTTP client for API calls

## Key Features

- Hybrid processing: deterministic rules + AI intelligence
- Cost-efficient: minimal API calls through smart batching
- Privacy-focused: educational use only, no data storage
- Multi-format support: various bank statement layouts

## Setup

1. Clone repository and install dependencies
2. Add Anthropic API key to `.env` file
3. Run analysis on your bank statements
4. Get instant spending insights and categorization

---
*Built with a focus on efficiency, accuracy, and financial privacy.*