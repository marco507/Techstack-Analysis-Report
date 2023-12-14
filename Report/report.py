import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import itertools
from mlxtend.frequent_patterns import apriori

class Report():

    def __init__(self):
        st.title('Techstack Analysis Report')

    @st.cache_data
    def get_database_stats(_self):
        
        con = sqlite3.connect('data.db')
        cur = con.cursor()

        data = dict()

        # Get websites
        data['Websites'] = cur.execute("""SELECT COUNT(ID) FROM Website""")
        data['Websites']  = data['Websites'].fetchall()[0][0]

        # Get branches
        data['Branches']  = cur.execute("""SELECT COUNT(DISTINCT Branche) FROM Website""")
        data['Branches']  = data['Branches'].fetchall()[0][0]

        # Get technologies
        data['Technologies'] = cur.execute("""SELECT COUNT(ID) FROM Technology""")
        data['Technologies'] = data['Technologies'].fetchall()[0][0]

        # Get categories
        data['Categories']  = cur.execute("""SELECT COUNT(ID) FROM Category""")
        data['Categories']  = data['Categories'] .fetchall()[0][0]

        con.close()

        return data
    
    def plot_database_stats(_self):

        data = _self.get_database_stats()

        st.markdown("""Analyzing what different technologies are used by websites can provide valuable 
                    insights for businesses looking to gain a competitive edge in the digital realm. 
                    By examining these technology stacks, we can uncover potential leads, identify market trends,
                    and make informed strategic decisions. This interactive report is based on a self-compiled dataset 
                    of business websites with the following statistics:
                    """)

        with st.container(border=True):
            columns = st.columns(4)

            for i, items in enumerate(data.items()):
                    with columns[i]:
                        st.metric(items[0], items[1])

    @st.cache_data
    def get_websites_per_branch(_self):

        con = sqlite3.connect('data.db')
        cur = con.cursor()

        data = cur.execute(
            """
            SELECT Branche, COUNT(ID) AS TotalCount,
            ROUND(CAST((COUNT(ID) * 100.0 / (SELECT COUNT(*) FROM Website)) AS FLOAT), 1) AS Percentage
            FROM Website
            GROUP BY Branche;
            """)
    
        data = data.fetchall()
        data = pd.DataFrame(data, columns=['Branch', 'Websites', 'Percentage'])
        data.index += 1

        con.close()

        return data
    
    def plot_websites_per_branch(_self):

        data = _self.get_websites_per_branch()

        st.markdown("The websites are evenly distributed over 10 branches as can be seen in the chart below.")

        with st.container(border=True):
            fig = px.pie(data, values='Percentage', names='Branch',
                    title='Website distribution over branches',
                    hover_data=['Websites'], labels={'Websites':'Number of websites'})

            st.plotly_chart(fig, theme="streamlit", use_container_width=True)

    @st.cache_data
    def get_branch_aggregations(_self, group, aggregation, limit):

        if aggregation == 'All branches':
            if group == 'Technologies':
                query = """
                SELECT Technology.Name, COUNT(Website.ID) FROM Website 
                INNER JOIN Website_Technology ON Website.ID = Website_Technology.WebsiteID
                INNER JOIN Technology on Technology.ID = Website_Technology.TechnologyID
                GROUP BY Technology.Name
                ORDER BY COUNT(Website.ID) DESC
                LIMIT ?;
                """

            elif group == 'Categories':
                query ="""
                SELECT Category.Name, COUNT(DISTINCT Website.ID) FROM Website 
                INNER JOIN Website_Technology ON Website.ID = Website_Technology.WebsiteID
                INNER JOIN Technology on Technology.ID = Website_Technology.TechnologyID
                INNER JOIN Technology_Category on Technology.ID = Technology_Category.TechnologyID
                INNER JOIN Category on Category.ID = Technology_Category.CategoryID
                GROUP BY Category.Name
                ORDER BY COUNT(DISTINCT Website.ID) DESC
                LIMIT ?;
                """
        else:
            if group == 'Technologies':
                query =f"""
                SELECT Technology.Name, COUNT(Website.ID) FROM Website 
                INNER JOIN Website_Technology ON Website.ID = Website_Technology.WebsiteID
                INNER JOIN Technology on Technology.ID = Website_Technology.TechnologyID
                WHERE Website.Branche = "{aggregation}"
                GROUP BY Technology.Name
                ORDER BY COUNT(Website.ID) DESC
                LIMIT ?;
                """

            elif group == 'Categories':
                query =f"""
                SELECT Category.Name, COUNT(DISTINCT Website.ID) FROM Website 
                INNER JOIN Website_Technology ON Website.ID = Website_Technology.WebsiteID
                INNER JOIN Technology on Technology.ID = Website_Technology.TechnologyID
                INNER JOIN Technology_Category on Technology.ID = Technology_Category.TechnologyID
                INNER JOIN Category on Category.ID = Technology_Category.CategoryID
                WHERE Website.Branche = "{aggregation}"
                GROUP BY Category.Name
                ORDER BY COUNT(DISTINCT Website.ID) DESC
                LIMIT ?;
                """

        con = sqlite3.connect('data.db')
        cur = con.cursor()

        data = cur.execute(query, (limit,))
        data = data.fetchall()
        
        data = pd.DataFrame(data, columns=[f'{group}', f'{aggregation}'])

        con.close()

        return data
        
    def plot_branch_aggregations(_self):

        @st.cache_data
        def get_branches():

            con = sqlite3.connect('data.db')
            cur = con.cursor()
            
            branches = cur.execute("SELECT DISTINCT Website.Branche FROM Website;")

            branches = branches.fetchall()
            branches = pd.DataFrame(branches, columns=['Branch'])
            
            con.close()

            return branches


        st.markdown("""The first question that we try to answer with our data will be how often individual
                    technologies or technology categories are used throughout the dataset. For clarification, 
                    a technology is for example something like "jQuery" and the corresponding category would be
                    "JavaScript libraries".""")
        
        st.markdown("""There are three options to narrow down the data that interests you. 
                    First, you can choose how many technologies or categories are displayed by moving the slider.
                    Next you can decide if you want to show individual technologies or technology categories
                    with the first dropdown menu. With the second dropdown, you can select a specific industry branch 
                    or if the usage count should be taken over all branches.""")
        
        st.markdown("""To show the data based on your selection
                    click the load button. The results are always plotted in descending order, meaning from highest to 
                    lowest usage count.""")
        
        with st.form('data_selection'):
            limit = st.slider('Top', 5, 25, 5)
            
            groups = ['Technologies', 'Categories']
            group_selection = st.selectbox(label='Group', options=groups, label_visibility='collapsed')

            branches = get_branches()
            aggregation_selection = st.selectbox('used in', ['All branches'] + branches['Branch'].to_list())

            submitted = st.form_submit_button("Load")
            
            if submitted:
                data = _self.get_branch_aggregations(group_selection, aggregation_selection, limit)
                fig = px.bar(data, x=group_selection, y=aggregation_selection,
                             labels={group_selection: group_selection, aggregation_selection: 'Usage count'})
                st.plotly_chart(fig, theme="streamlit", use_container_width=True)

    @st.cache_data
    def get_category_aggregations(_self, category):

        con = sqlite3.connect('data.db')
        cur = con.cursor()

        data = cur.execute(
            f"""
            SELECT Technology.Name, COUNT(Website.ID) FROM Technology
            INNER JOIN Website_Technology ON Technology.ID = Website_Technology.TechnologyID
            INNER JOIN Website on Website.ID = Website_Technology.WebsiteID
            INNER JOIN Technology_Category on Technology.ID = Technology_Category.TechnologyID
            INNER JOIN Category on Category.ID = Technology_Category.CategoryID
            WHERE Category.Name = "{category}"
            GROUP BY Technology.Name
            ORDER BY COUNT(Website.ID) DESC;
            """)
    
        data = data.fetchall()
        data = pd.DataFrame(data, columns=['Technology', 'UsageCount'])
        data.index += 1

        con.close()

        return data
    
    def plot_category_aggregations(_self):

        @st.cache_data
        def get_categories():
            con = sqlite3.connect('data.db')
            cur = con.cursor()

            data = cur.execute('SELECT Name FROM Category')
        
            data = data.fetchall()
            data = pd.DataFrame(data, columns=['Category'])
            data.index += 1

            con.close()

            return data
        
        st.markdown("""On this page, we take a detailed look into the composition of the technology categories.
                    You can select multiple categories of interest and click the load button to 
                    see what technologies are most often used in the respective category. Each category is shown in
                    a separate tab.""")
        
        with st.form('data_selection'):
            categories = get_categories()
            categories = st.multiselect('Categories', categories, max_selections=6)

            submitted = st.form_submit_button("Load")
            if submitted and categories:
                
                tabs = st.tabs(categories)

                for i, category in enumerate(categories):

                    data = _self.get_category_aggregations(category)
                    fig = go.Figure(data=[go.Pie(labels=data['Technology'].to_list(), values=data['UsageCount'].to_list(), hole=.8)])
                    fig.update_traces(textposition='inside')
                    fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide')

                    tabs[i].plotly_chart(fig, theme="streamlit", use_container_width=True)

    @st.cache_data
    def get_stack_data(_self):
            
        con = sqlite3.connect('data.db')
        cur = con.cursor()

        data = cur.execute(
            """
            SELECT Website.Link, GROUP_CONCAT(Technology.Name, ',') AS Techstacks FROM Website
            INNER JOIN Website_Technology ON Website.ID = Website_Technology.WebsiteID
            INNER JOIN Technology ON Technology.ID = Website_Technology.TechnologyID
            GROUP BY Website.Link;
            """)
    
        data = data.fetchall()
        con.close()

        data = pd.DataFrame(data, columns=['Website', 'Techstacks'])
        stacks = data['Techstacks'].to_list()
        columns = [stack.split(',') for stack in stacks]
        columns = list(itertools.chain.from_iterable(columns))
        columns = list(set(columns))

        rows = []
        one_hot_df = pd.DataFrame(columns=columns)

        for stack in stacks:

            # Init empty row
            row = pd.Series([False]*(len(columns)), index=one_hot_df.columns)

            for tech in stack.split(','):
                row[tech] = True
                    
            rows.append(row)
            
        data = pd.DataFrame(rows)
        
        return data
    

    def plot_stack_data(_self):
        
        data = _self.get_stack_data()

        st.markdown("""Finally, we can examine the technology stacks which are generated with the Apriori algorithm.
                    The algorithm was developed to extract frequent item sets, for example, store items that are often
                    bought together. We use it here to uncover web technologies that are frequently employed as a stack.""") 
                    
        st.markdown("""To discover possible tech stacks, first choose the number of technologies that should comprise a stack.
                    This would be the size of our item set. Next, enter the percentage of how many records in our database must
                    contain a certain combination of technologies to be considered a stack. This value is called the support.""")

        st.markdown("""To illustrate this, look at the pre-set values below. If you click on the load button, you will get
                    item sets or in our case tech stacks that contain three technologies which appear together in 25 percent of
                    all websites in our database.""")  

        
        with st.form('data_selection'):
            items = st.slider('Number of items in a stack', min_value=2, max_value=6, value=3)
            support = st.number_input('Percentage of websites (Support)', min_value=1, max_value=100, value=25)

            frequent_itemsets = apriori(data, min_support=support/100, use_colnames=True)
            frequent_itemsets['length'] = frequent_itemsets['itemsets'].apply(lambda x: len(x))

            frequent_itemsets = frequent_itemsets[ 
                (frequent_itemsets['length'] >= items) & (frequent_itemsets['support'] >= support/100)]

            frequent_itemsets = frequent_itemsets.sort_values(by='support', ascending=False)
            frequent_itemsets['itemsets'] = frequent_itemsets['itemsets'].apply(lambda x: '-'.join(x))
            frequent_itemsets['support'] = frequent_itemsets['support'].apply(lambda x: round(x * 100, 1))

            submitted = st.form_submit_button("Load")
            if submitted:
                if frequent_itemsets['itemsets'].to_list():
                    fig = px.bar(frequent_itemsets, x='itemsets', y='support',
                                 labels={'itemsets': 'Techstacks', 'support': 'Percentage of websites using the stack'})
                    st.plotly_chart(fig, theme="streamlit", use_container_width=True)
                
                else:
                    st.write('There are no techstacks with the given parameters.')