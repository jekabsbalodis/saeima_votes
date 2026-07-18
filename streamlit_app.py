"""Main entry for streamlit app displaying voting statistics."""

import duckdb
import streamlit as st

con = duckdb.connect()

con.execute(
    """--sql
            install httpfs;
            load httpfs;
            create or replace secret (
               type s3,
               key_id ?,
               secret ?,
               endpoint ?,
               region ?,
               url_style 'path'
             );""",
    (
        st.secrets.garage.GARAGE_KEY_ID,
        st.secrets.garage.GARAGE_KEY_SECRET,
        st.secrets.garage.GARAGE_ENDPOINT,
        st.secrets.garage.GARAGE_REGION,
    ),
)

st.write('# Neapstrādāti dati')

df = con.execute("""--sql
                 select * from read_parquet('s3://saeima-votes/raw.dkp.parquet')""").pl()

df_len = len(df)

st.write(f'## 14.&nbsp;Saeimas sesiju darba kārtības; {df_len} ieraksti')

st.dataframe(df)

df2 = con.execute("""--sql
                 select * from read_parquet('s3://saeima-votes/raw.dkp_items.parquet')""").pl()

df2_len = len(df2)

st.write(f'## 14.&nbsp;Saeimas sesiju darba kārtību punkti; {df2_len} ieraksti')

st.dataframe(df2)

df3 = con.execute("""--sql
                 select * from read_parquet('s3://saeima-votes/raw.vote.parquet')""").pl()

df3_len = len(df3)

st.write(f'## 14.&nbsp;Saeimas balsošanas dati; {df3_len} ieraksti')

st.dataframe(df3)

df4 = con.execute("""--sql
                 select * from read_parquet('s3://saeima-votes/raw.debate.parquet')""").pl()

df4_len = len(df4)

st.write(f'## 14.&nbsp;Saeimas debašu dati; {df4_len} ieraksti')

st.dataframe(df4)

st.write('# Dimensiju tabulas')

st.write('## Sesiju tipi')

df5 = con.execute("""--sql
                 select * from read_parquet('s3://saeima-votes/dim.session_type.parquet')""").pl()

st.dataframe(df5)
