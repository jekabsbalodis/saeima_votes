import marimo

__generated_with = "0.23.14"
app = marimo.App()

with app.setup:
    import os

    import duckdb
    import httpx
    import marimo as mo
    import pandas as pd
    import polars as pl
    from dotenv import load_dotenv

    load_dotenv('.env')


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Database

    ## Create connection
    """)
    return


@app.cell
def _():
    _DATABASE_URL = 'explore_saeima.db'
    engine = duckdb.connect(_DATABASE_URL, read_only=False)
    return (engine,)


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Create schema `raw` and table for url tracking
    """)
    return


@app.cell
def _(engine):
    _df = mo.sql(
        f"""
        create schema if not exists raw;

        create table if not exists raw._loaded_urls (
            url varchar primary key,
            doc_type varchar, -- 'dkp', 'vote', 'deb'
            loaded_at timestamp default current_timestamp,
            had_data bool default true
        );
        """,
        engine=engine
    )
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Create schema `dim` and table for `session_type` dimension
    """)
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Data processing
    ## Create function to fetch all urls for data files
    """)
    return


@app.cell
def _():
    def get_all_resources(package_id: str) -> list[dict]:
        url = 'https://data.gov.lv/dati/api/3/action/package_show'
        response = httpx.get(url, params={'id': package_id})
        response.raise_for_status()
        data = response.json()
        return data['result']['resources']

    def extract_urls(
        resources: list[dict],
        suffix: str,
        must_contain: str,
    ) -> list[str]:
        return [
            r['url']
            for r in resources
            if r['url'].endswith(suffix) and must_contain in r['url']
        ]

    return extract_urls, get_all_resources


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Create functions to parse various types of urls
    """)
    return


@app.cell
def _():
    def read_agenda(url: str) -> pl.DataFrame:
        return pl.from_pandas(pd.read_xml(url, xpath='./DK', dtype=str))

    def read_agenda_items(url: str) -> pl.DataFrame:
        return pl.from_pandas(pd.read_xml(url, xpath='.//DKP', dtype=str))

    def read_votes(url: str) -> pl.DataFrame:
        return pl.from_pandas(pd.read_xml(url, xpath='.//VOTES', dtype=str))

    def read_debates(url: str) -> pl.DataFrame:
        return pl.from_pandas(pd.read_xml(url, xpath='.//DEBATES', dtype=str))

    return read_agenda, read_agenda_items, read_debates, read_votes


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Create function to create a list of DataFrames with data
    """)
    return


@app.cell
def _(extract_urls):
    def load_doc_type(
        resources: list[dict],
        suffix: str,
        must_contain: str,
        doc_type: str,
        reader,
        loaded_urls: list[str],
    ) -> tuple[pl.DataFrame, pl.DataFrame]:

        urls = extract_urls(resources, suffix, must_contain)
        to_process = [u for u in urls if u not in loaded_urls]

        frames: list[pl.DataFrame] = []
        loaded: list[dict] = []

        for url in mo.status.progress_bar(
            to_process, title=f'Loading {doc_type}...'
        ):
            try:
                df = reader(url)
                frames.append(df)
                loaded.append(
                    {'url': url, 'doc_type': doc_type, 'had_data': True}
                )
            except ValueError:
                loaded.append(
                    {'url': url, 'doc_type': doc_type, 'had_data': False}
                )

        data_df = pl.concat(frames, how='diagonal') if frames else None

        loaded_df = (
            pl.DataFrame(loaded)
            if loaded
            else pl.DataFrame(
                schema={
                    'url': pl.String,
                    'doc_type': pl.String,
                    'had_data': pl.Boolean,
                }
            )
        )

        return data_df, loaded_df

    return (load_doc_type,)


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Extract the data from the Saeima session info datasets
    """)
    return


@app.cell
def _(
    engine,
    get_all_resources,
    load_doc_type,
    read_agenda,
    read_agenda_items,
    read_debates,
    read_votes,
):
    _resources = get_all_resources('4f854a14-8861-449d-bb2a-832113734711')

    _loaded_urls = (
        engine.execute("""select url from raw._loaded_urls;""")
        .pl()
        .to_series()
        .to_list()
    )

    agendas_df, dkp_loaded_df = load_doc_type(
        _resources,
        'dkp.xml',
        '14.saeimas',
        'dkp',
        read_agenda,
        _loaded_urls,
    )
    agenda_items_df, _ = load_doc_type(
        _resources,
        'dkp.xml',
        '14.saeimas',
        'dkp',
        read_agenda_items,
        _loaded_urls,
    )
    votes_df, vote_loaded_df = load_doc_type(
        _resources,
        'vote.xml',
        '14.saeimas',
        'vote',
        read_votes,
        _loaded_urls,
    )
    debates_df, debate_loaded_df = load_doc_type(
        _resources,
        'deb.xml',
        '14.saeimas',
        'deb',
        read_debates,
        _loaded_urls,
    )
    return (
        agenda_items_df,
        agendas_df,
        debate_loaded_df,
        debates_df,
        dkp_loaded_df,
        vote_loaded_df,
        votes_df,
    )


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Data loading
    ## Create tables for the raw data
    """)
    return


@app.cell
def _(agenda_items_df, agendas_df, debates_df, engine, votes_df):
    if agendas_df is not None:
        engine.execute(
            """
            create table if not exists raw.dkp as
            select
                *
            from
                agendas_df
            where
                1 = 0;
            """
        )

    if agenda_items_df is not None:
        engine.execute(
            """
            create table if not exists raw.dkp_items as
            select
                *
            from
                agenda_items_df
            where
                1 = 0;
            """
        )

    if votes_df is not None:
        engine.execute(
            """
            create table if not exists raw.vote as
            select
                *
            from
                votes_df
            where
                1 = 0;
            """
        )

    if debates_df is not None:
        engine.execute(
            """
            create table if not exists raw.debate as
            select
                *
            from
                debates_df
            where
                1 = 0;
            """
        )
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Add primary key constraints
    """)
    return


@app.cell
def _(engine):
    try:
        engine.execute(
            """alter table raw.dkp
            add constraint dkp_pk primary key ("WORKSEQUENCEID");"""
        )
    except duckdb.CatalogException:
        pass

    try:
        engine.execute(
            """alter table raw.dkp_items
            add constraint dkp_items_pk primary key ("DKP_ID");"""
        )
    except duckdb.CatalogException:
        pass

    try:
        engine.execute(
            """alter table raw.vote
            add constraint vote_pk primary key ("VOTING_ID");"""
        )
    except duckdb.CatalogException:
        pass

    try:
        engine.execute(
            """alter table raw.debate
            add constraint debates_pk primary key ("DKP_ID");"""
        )
    except duckdb.CatalogException:
        pass
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Load data into tables
    """)
    return


@app.cell
def _(agenda_items_df, agendas_df, debates_df, engine, votes_df):
    if agendas_df is not None:
        engine.execute(
            """
            insert or ignore into raw.dkp 
            select
                *
            from
                agendas_df;
            """
        )

    if agenda_items_df is not None:
        engine.execute(
            """
            insert or ignore into raw.dkp_items
            select
                *
            from
                agenda_items_df;
            """
        )

    if votes_df is not None:
        engine.execute(
            """
            insert or ignore into raw.vote
            select
                *
            from
                votes_df;
            """
        )

    if debates_df is not None:
        engine.execute(
            """
            insert or ignore into raw.debate
            select
                *
            from
                debates_df;
            """
        )
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Write info about loaded urls into databse
    """)
    return


@app.cell
def _(debate_loaded_df, dkp_loaded_df, engine, vote_loaded_df):
    loaded_urls_df = pl.concat(
        [dkp_loaded_df, vote_loaded_df, debate_loaded_df], how='diagonal'
    )

    engine.execute(
        """
            insert or ignore into raw._loaded_urls (
                url,
                doc_type,
                had_data
            )
            select
                url,
                doc_type,
                had_data
            from
                loaded_urls_df;
            """
    )
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Write data to S3 storage
    ## Create S3 connection in database
    """)
    return


@app.cell
def _(engine):
    _df = mo.sql(
        f"""
        install httpfs;
        load httpfs;
        """,
        engine=engine
    )
    return


@app.cell
def _(engine):
    engine.execute(
        """
        create or replace secret (
           type s3,
           key_id ?,
           secret ?,
           endpoint ?,
           region ?,
           url_style 'path'
         );
    """,
        (
            os.environ.get('GARAGE_KEY_ID'),
            os.environ.get('GARAGE_KEY_SECRET'),
            os.environ.get('GARAGE_ENDPOINT'),
            os.environ.get('GARAGE_REGION'),
        ),
    )
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Copy tables to S3 storage as parquet files
    """)
    return


@app.cell
def _(engine):
    _df = mo.sql(
        f"""
        copy (
            select
                *
            from
                dim.session_type
        ) to 's3://saeima-votes/dim.session_type.parquet' (format parquet, overwrite_or_ignore true);

        copy (
            select
                *
            from
                raw._loaded_urls
        ) to 's3://saeima-votes/raw._loaded_urls.parquet' (format parquet, overwrite_or_ignore true);

        copy (
            select
                *
            from
                raw.debate
        ) to 's3://saeima-votes/raw.debate.parquet' (format parquet, overwrite_or_ignore true);

        copy (
            select
                *
            from
                raw.dkp
        ) to 's3://saeima-votes/raw.dkp.parquet' (format parquet, overwrite_or_ignore true);

        copy (
            select
                *
            from
                raw.dkp_items
        ) to 's3://saeima-votes/raw.dkp_items.parquet' (format parquet, overwrite_or_ignore true);

        copy (
            select
                *
            from
                raw.vote
        ) to 's3://saeima-votes/raw.vote.parquet' (format parquet, overwrite_or_ignore true);
        """,
        engine=engine
    )
    return


if __name__ == "__main__":
    app.run()
