import streamlit as st

index_historical = st.Page(
    "index_dashboard/index_distribution.py", title="Index Historical Performance", icon=":material/dashboard:", default=False
)

index_movements = st.Page(
    "index_dashboard/index_movements.py", title="Index Movement", icon=":material/dashboard:", default=True
)

index_deepdive = st.Page(
    "index_dashboard/index_deepdive.py", title="Index Deepdive", icon=":material/query_stats:", default=False
)

st.set_page_config(layout="wide")
st.markdown("""
    <style>
    
           /* Remove blank space at top and bottom */ 
           .block-container {
               padding-top: 1.5rem;
               padding-bottom: 0rem;
            }
           
           /* Remove blank space at the center canvas */ 
           .st-emotion-cache-z5fcl4 {
               position: relative;
               top: -62px;
               }
           
           /* Make the toolbar transparent and the content below it clickable */ 
           .st-emotion-cache-18ni7ap {
               pointer-events: none;
               background: rgb(255 255 255 / 0%)
               }
           .st-emotion-cache-zq5wmm {
               pointer-events: auto;
               background: rgb(255 255 255);
               border-radius: 5px;
               }
    </style>
    """, unsafe_allow_html=True)


# pg = st.navigation(
#     {
#      "Index Movement": [index_movements],
#      "Index Historical Performance": [index_historical],
#      "Index Deepdive": [index_deepdive],

#      }
# )

pg = st.navigation(
    [index_movements,
     index_historical,
     index_deepdive,
    ]
)

 # Create a container for the header and logo
header_container = st.container()

# Use columns to align the title and logo
left_column, right_column = header_container.columns([3, 1])

with left_column:
    st.title(f"Index 360/{pg.title}")

with right_column:
# Adjust width as needed
    st.image("bds_transparent_logo.png", width=120)
pg.run()
