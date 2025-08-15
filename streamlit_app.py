"""
Bank Statement Analyzer - Streamlit UI
=====================================

Beautiful web interface for your hybrid multi-agent system
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

# Import your system
from main_coordinator import BankStatementAnalyzer

def initialize_session_state():
    """Initialize Streamlit session state"""
    if 'analyzer' not in st.session_state:
        load_dotenv()
        api_key = os.getenv('ANTHROPIC_API_KEY')
        
        if api_key:
            with st.spinner("🏗️ Initializing 3-agent system..."):
                st.session_state.analyzer = BankStatementAnalyzer(api_key)
            st.success("✅ System ready!")
        else:
            st.session_state.analyzer = None
            st.error("❌ Please set ANTHROPIC_API_KEY in .env file")

def main():
    """Main Streamlit application"""
    
    # Page configuration
    st.set_page_config(
        page_title="Bank Statement Analyzer",
        page_icon="🏦",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session
    initialize_session_state()
    
    # Main header
    st.title("🏦 Bank Statement Analyzer")
    st.subheader("Hybrid Multi-Agent Financial Analysis System")
    
    # Educational warning
    st.warning("⚠️ **Educational Project Only** - Do not use with real financial data containing sensitive information")
    
    # Sidebar - System Information
    with st.sidebar:
        st.header("🤖 System Status")
        
        if st.session_state.analyzer:
            st.success("✅ All agents initialized")
            
            # Agent information
            st.subheader("Agent Architecture")
            st.write("🏗️ **Agent 1**: Document Processor")
            st.caption("Extracts & parses PDF (0 LLM calls)")
            
            st.write("🧠 **Agent 2**: Content Analyzer") 
            st.caption("Smart categorization (1 LLM call)")
            
            st.write("📊 **Agent 3**: Analysis Generator")
            st.caption("Financial insights (0-1 LLM calls)")
            
            st.divider()
            
            # Project info
            st.subheader("Project Details")
            st.write("**Course**: CSYE 7374")
            st.write("**Type**: Hybrid Multi-Agent System")
            st.write("**Efficiency**: ≤2 LLM calls per analysis")
            
        else:
            st.error("❌ System initialization failed")
            st.write("Please check your .env file contains ANTHROPIC_API_KEY")
    
    # Main content area
    if not st.session_state.analyzer:
        st.error("System not initialized. Please check your API key configuration.")
        return
    
    # File upload section
    st.header("📄 Upload Bank Statement")
    
    uploaded_file = st.file_uploader(
        "Choose a bank statement PDF file",
        type=['pdf'],
        help="Upload your bank statement PDF for automated analysis"
    )
    
    if uploaded_file:
        # Show file info
        st.info(f"📄 **File**: {uploaded_file.name} ({uploaded_file.size:,} bytes)")
        
        # Analysis options
        col1, col2 = st.columns(2)
        
        with col1:
            generate_insights = st.checkbox(
                "🤖 Generate AI Insights",
                value=False,
                help="Use additional LLM call for personalized financial recommendations"
            )
        
        with col2:
            if generate_insights:
                st.info("📊 Will use 2 LLM calls (~$0.004)")
            else:
                st.info("📊 Will use 1 LLM call (~$0.002)")
        
        # Analysis button
        if st.button("🚀 Analyze Statement", type="primary", use_container_width=True):
            process_uploaded_file(uploaded_file, generate_insights)
    
    else:
        # Instructions when no file uploaded
        st.info("👆 Please upload a bank statement PDF to begin analysis")
        
        # Sample files section
        st.subheader("📋 Sample Files Available")
        st.write("You can test with these sample bank statements:")
        
        sample_files = [
            "chase_statement.pdf - Chase Bank format",
            "Sample Bank Statement.pdf - Generic format", 
            "Wells Fargo Statement.pdf - Wells Fargo format"
        ]
        
        for sample in sample_files:
            st.write(f"• {sample}")

def process_uploaded_file(uploaded_file, generate_insights: bool):
    """Process the uploaded file and show results"""
    
    # Save uploaded file temporarily
    temp_path = f"temp_{uploaded_file.name}"
    
    try:
        # Write uploaded file to disk
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Create processing progress
        progress_container = st.container()
        
        with progress_container:
            st.subheader("🔄 Processing Pipeline")
            
            # Progress indicators
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Agent processing steps
            agent_cols = st.columns(3)
            
            with agent_cols[0]:
                agent1_status = st.empty()
                agent1_status.info("🏗️ Agent 1: Waiting...")
            
            with agent_cols[1]:
                agent2_status = st.empty()
                agent2_status.info("🧠 Agent 2: Waiting...")
            
            with agent_cols[2]:
                agent3_status = st.empty()
                agent3_status.info("📊 Agent 3: Waiting...")
            
            # Step 1: Agent 1
            status_text.text("🏗️ Agent 1: Processing PDF...")
            agent1_status.warning("🏗️ Agent 1: Processing PDF...")
            progress_bar.progress(20)
            
            # Step 2: Agent 2
            status_text.text("🧠 Agent 2: Smart categorization...")
            agent1_status.success("🏗️ Agent 1: ✅ Complete")
            agent2_status.warning("🧠 Agent 2: Categorizing...")
            progress_bar.progress(60)
            
            # Step 3: Agent 3
            if generate_insights:
                status_text.text("📊 Agent 3: Generating AI insights...")
            else:
                status_text.text("📊 Agent 3: Generating analysis...")
            
            agent2_status.success("🧠 Agent 2: ✅ Complete") 
            agent3_status.warning("📊 Agent 3: Analyzing...")
            progress_bar.progress(90)
            
            # Run the actual analysis
            result = st.session_state.analyzer.analyze_statement(
                temp_path,
                generate_ai_insights=generate_insights
            )
            
            # Complete
            agent3_status.success("📊 Agent 3: ✅ Complete")
            progress_bar.progress(100)
            status_text.text("✅ Analysis complete!")
        
        # Display results
        if result['success']:
            st.success("🎉 Analysis completed successfully!")
            display_results(result)
        else:
            st.error(f"❌ Analysis failed: {result['error']}")
    
    except Exception as e:
        st.error(f"❌ Error processing file: {str(e)}")
    
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)

def display_results(result: dict):
    """Display beautiful analysis results"""
    
    # Extract data
    analysis = result['analysis']
    summary = analysis['financial_summary']
    categories = analysis['category_breakdown']
    metrics = result['system_metrics']
    
    st.header("📊 Financial Analysis Results")
    
    # Key metrics in cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💰 Total Spent",
            f"${summary['total_spent']:.2f}",
            delta=f"{summary['debit_count']} transactions"
        )
    
    with col2:
        st.metric(
            "💵 Total Income", 
            f"${summary['total_income']:.2f}",
            delta=f"{summary['credit_count']} deposits"
        )
    
    with col3:
        net_change = summary['net_change']
        st.metric(
            "📊 Net Change",
            f"${net_change:.2f}",
            delta="Positive" if net_change > 0 else "Negative",
            delta_color="normal" if net_change > 0 else "inverse"
        )
    
    with col4:
        st.metric(
            "🤖 System Efficiency",
            f"{metrics['total_llm_calls']}/2 LLM calls",
            delta=f"${metrics['estimated_cost']:.4f} cost"
        )
    
    # Charts section
    if categories:
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.subheader("🏷️ Spending by Category")
            
            # Create pie chart data
            category_names = [cat['category'].replace('_', ' ').title() for cat in categories]
            category_amounts = [cat['total'] for cat in categories]
            
            fig_pie = px.pie(
                values=category_amounts,
                names=category_names,
                title="Spending Distribution"
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with chart_col2:
            st.subheader("📈 Category Breakdown")
            
            # Create bar chart
            df_categories = pd.DataFrame([
                {
                    'Category': cat['category'].replace('_', ' ').title(),
                    'Amount': cat['total'],
                    'Percentage': cat['percentage'],
                    'Count': cat['transaction_count']
                }
                for cat in categories[:6]  # Top 6 categories
            ])
            
            fig_bar = px.bar(
                df_categories,
                x='Category',
                y='Amount', 
                title="Top Categories by Amount",
                text='Amount',
                color='Percentage',
                color_continuous_scale='Viridis'
            )
            fig_bar.update_traces(texttemplate='$%{text:.0f}', textposition='outside')
            fig_bar.update_layout(showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
    
    # Insights sections
    insight_col1, insight_col2 = st.columns(2)
    
    with insight_col1:
        st.subheader("💡 Financial Insights")
        for insight in analysis['basic_insights']:
            st.write(f"• {insight}")
    
    with insight_col2:
        if analysis.get('ai_insights') and analysis['ai_insights']:
            st.subheader("🤖 AI Recommendations")
            for insight in analysis['ai_insights'][:5]:  # Limit to 5
                if insight.strip():  # Only show non-empty insights
                    st.write(f"• {insight}")
        else:
            st.info("🤖 Enable 'Generate AI Insights' for personalized recommendations")
    
    # Transaction details (expandable)
    with st.expander("📋 View All Transactions", expanded=False):
        if result['transactions']:
            # Convert to DataFrame
            df_transactions = pd.DataFrame([
                {
                    'Date': txn['date'],
                    'Description': txn['description'][:40] + ('...' if len(txn['description']) > 40 else ''),
                    'Category': txn['category'].replace('_', ' ').title(),
                    'Amount': txn['amount'],
                    'Type': 'OUT' if txn['is_debit'] else 'IN',
                    'Confidence': f"{txn['confidence']:.0%}",
                    'Source': txn['source'].title()
                }
                for txn in result['transactions']
            ])
            
            st.dataframe(
                df_transactions,
                use_container_width=True,
                column_config={
                    'Amount': st.column_config.NumberColumn(
                        'Amount',
                        format='$%.2f'
                    ),
                    'Date': st.column_config.DateColumn('Date'),
                }
            )

if __name__ == "__main__":
    main()