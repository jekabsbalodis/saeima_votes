# /// script
# dependencies = [
#     "altair==6.2.2",
#     "duckdb==1.5.4",
#     "httpx==0.28.1",
#     "lxml==6.1.1",
#     "marimo",
#     "pandas==3.0.3",
#     "polars[pyarrow]==1.42.1",
#     "ruff==0.15.20",
#     "sqlglot==30.12.0",
#     "ty==0.0.55",
# ]
# requires-python = ">=3.14"
# ///

import marimo

__generated_with = "0.23.13"
app = marimo.App(width="medium", auto_download=["html"])


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import pandas as pd
    import polars as pl
    import duckdb
    import httpx

    return duckdb, httpx, mo, pd, pl


@app.cell(hide_code=True)
def _(duckdb):
    _DATABASE_URL = './db.db'
    engine = duckdb.connect(_DATABASE_URL, read_only=False)
    return (engine,)


@app.cell(hide_code=True)
def _(engine, mo):
    _df = mo.sql(
        f"""
        create schema if not exists raw;

        create table if not exists raw._loaded_urls (
            url varchar primary key,
            doc_type varchar, -- 'dkp', 'vote', 'deb'
            loaded_at timestamp default current_timestamp
        );

        create table if not exists raw._skipped_urls (
            url varchar primary key,
            doc_type VARCHAR, -- 'dkp', 'vote', 'deb'
            skipped_at timestamp default current_timestamp
        );

        create schema if not exists dim;

        create table if not exists dim.session_type (id UINT8 PRIMARY key, name VARCHAR);

        insert
        or ignore into dim.session_type (id, NAME)
        values
            (1, 'Kārtējā'),
            (2, 'Ārkārtas sēde'),
            (3, 'Svinīgā sēde'),
            (5, 'Atbilžu sniegšana uz deputātu jautājumiem'),
            (6, 'Ārkārtas sesijas sēde');
        """,
        output=False,
        engine=engine
    )
    return


@app.cell(hide_code=True)
def _(httpx, pd, pl):
    def read_agenda(url: str) -> pl.DataFrame:
        return pl.from_pandas(pd.read_xml(url, xpath='./DK', dtype=str))

    def read_agenda_items(url: str) -> pl.DataFrame:
        return pl.from_pandas(pd.read_xml(url, xpath='.//DKP', dtype=str))

    def read_votes(url: str) -> pl.DataFrame:
        return pl.from_pandas(pd.read_xml(url, xpath='.//VOTES', dtype=str))

    def read_debates(url: str) -> pl.DataFrame:
        return pl.from_pandas(pd.read_xml(url, xpath='.//DEBATES', dtype=str))

    def get_all_resources(package_id: str) -> list[dict]:
        url = 'https://data.gov.lv/dati/api/3/action/package_show'
        response = httpx.get(url, params={'id': package_id})
        response.raise_for_status()
        data = response.json()
        return data['result']['resources']

    return (
        get_all_resources,
        read_agenda,
        read_agenda_items,
        read_debates,
        read_votes,
    )


@app.cell(hide_code=True)
def _(
    engine,
    get_all_resources,
    mo,
    pl,
    read_agenda,
    read_agenda_items,
    read_debates,
    read_votes,
):
    _resources = get_all_resources('4f854a14-8861-449d-bb2a-832113734711')
    _dkp_files = [
        _r['url']
        for _r in _resources
        if (_r['url'].endswith('dkp.xml') and '14.saeimas' in _r['url'])
    ]

    _vote_files = [
        _r['url']
        for _r in _resources
        if (_r['url'].endswith('vote.xml') and '14.saeimas' in _r['url'])
    ]

    _debate_files = [
        _r['url']
        for _r in _resources
        if (_r['url'].endswith('deb.xml') and '14.saeimas' in _r['url'])
    ]

    _loaded_urls = (
        engine.execute("""select url from raw._loaded_urls;""")
        .pl()
        .to_series()
        .to_list()
    )

    _agendas, _agenda_items, _loaded, _skipped = [], [], [], []

    _i = 0
    for _url in mo.status.progress_bar(_dkp_files):
        if _url in _loaded_urls and _i > 0:
            continue
        _agendas.append(read_agenda(_url))
        _agenda_items.append(read_agenda_items(_url))
        _loaded.append({'url': _url, 'doc_type': 'dkp'})
        _i = _i + 1

    _votes = []

    _i = 0
    for _url in mo.status.progress_bar(_vote_files):
        if _url in _loaded_urls and _i > 0:
            continue
        try:
            _votes.append(read_votes(_url))
            _i = _i + 1
        except ValueError:
            _skipped.append({'url': _url, 'doc_type': 'vote'})
        _loaded.append({'url': _url, 'doc_type': 'vote'})

    _debates = []

    _i = 0
    for _url in mo.status.progress_bar(_debate_files):
        if _url in _loaded_urls and _i > 0:
            continue
        try:
            _debates.append(read_debates(_url))
            _i = _i + 1
        except ValueError:
            _skipped.append({'url': _url, 'doc_type': 'deb'})
        _loaded.append({'url': _url, 'doc_type': 'deb'})

    agendas_df = pl.concat(_agendas, how='diagonal')
    agenda_items_df = pl.concat(_agenda_items, how='diagonal')
    votes_df = pl.concat(_votes, how='diagonal')
    debates_df = pl.concat(_debates, how='diagonal')
    loaded_urls_df = pl.DataFrame(_loaded)
    skipped_urls_df = pl.DataFrame(_skipped)
    return (
        agenda_items_df,
        agendas_df,
        debates_df,
        loaded_urls_df,
        skipped_urls_df,
        votes_df,
    )


@app.cell(hide_code=True)
def _(agenda_items_df, agendas_df, debates_df, engine, mo, votes_df):
    _df = mo.sql(
        f"""
        create table if not exists raw.dkp as
        select
            *
        from
            agendas_df
        where
            1 = 0;

        create table if not exists raw.dkp_items as
        select
            *
        from
            agenda_items_df
        where
            1 = 0;

        create table if not exists raw.vote as
        select
            *
        from
            votes_df
        where
            1 = 0;

        create table if not exists raw.debate as
        select
            *
        from
            debates_df
        where
            1 = 0;
        """,
        output=False,
        engine=engine
    )
    return


@app.cell(hide_code=True)
def _(duckdb, engine):
    try:
        engine.execute(
            """alter table raw.dkp add constraint dkp_pk primary key ("WORKSEQUENCEID");"""
        )
    except duckdb.CatalogException:
        pass
    try:
        engine.execute(
            """alter table raw.dkp_items add constraint dkp_items_pk primary key ("DKP_ID");"""
        )
    except duckdb.CatalogException:
        pass
    try:
        engine.execute(
            """alter table raw.vote add constraint vote_pk primary key ("VOTING_ID");"""
        )
    except duckdb.CatalogException:
        pass
    try:
        engine.execute(
            """alter table raw.debate add constraint debates_pk primary key ("DKP_ID");"""
        )
    except duckdb.CatalogException:
        pass
    return


@app.cell(hide_code=True)
def _(
    agenda_items_df,
    agendas_df,
    debates_df,
    engine,
    loaded_urls_df,
    mo,
    skipped_urls_df,
    votes_df,
):
    _df = mo.sql(
        f"""
        insert
        or ignore into raw.dkp
        select
            *
        from
            agendas_df;

        insert
        or ignore into raw.dkp_items
        select
            *
        from
            agenda_items_df;

        insert
        or ignore into raw.vote
        select
            *
        from
            votes_df;

        insert
        or ignore into raw.debate
        select
            *
        from
            debates_df;

        insert
        or ignore into raw._loaded_urls (url, doc_type)
        select
            url,
            doc_type
        from
            loaded_urls_df;

        insert
        or ignore into raw._skipped_urls (url, doc_type)
        select
            url,
            doc_type
        from
            skipped_urls_df;
        """,
        output=False,
        engine=engine
    )
    return


@app.cell(hide_code=True)
def _(engine, mo):
    _df = mo.sql(
        f"""
        SELECT
            *
        FROM
            raw.dkp
        order by
            DK_NUMBER desc;
        """,
        engine=engine
    )
    return


@app.cell(hide_code=True)
def _(engine, mo):
    _df = mo.sql(
        f"""
        select distinct SESSIONNAME, strptime(SESSIONSTARTDATE, '%d.%m.%Y') as session_start_date, PARLAMENTNUMBER::uint8 from raw.dkp;
        """,
        engine=engine
    )
    return


@app.cell(hide_code=True)
def _(engine, mo):
    _df = mo.sql(
        f"""
        SELECT
            SESSIONTYPE,
            STATUS,
            DKENDTIME IS NULL AS end_time_missing,
            COUNT(*)
        FROM
            raw.dkp
        GROUP BY
            SESSIONTYPE,
            STATUS,
            end_time_missing
        ORDER BY
            SESSIONTYPE,
            STATUS;
        """,
        engine=engine
    )
    return


@app.cell(hide_code=True)
def _(engine, mo):
    _df = mo.sql(
        f"""
        select
            *
        from
            raw.dkp_items
        where result_ispositive is NULL;
        """,
        engine=engine
    )
    return


@app.cell(hide_code=True)
def _(engine, mo):
    _df = mo.sql(
        f"""
        select
            *
        from
            raw.vote;
        """,
        engine=engine
    )
    return


@app.cell(hide_code=True)
def _(engine, mo):
    _df = mo.sql(
        f"""
        select * from raw.debate;
        """,
        engine=engine
    )
    return


@app.cell(hide_code=True)
def _(engine, mo):
    _df = mo.sql(
        f"""
        checkpoint;
        """,
        output=False,
        engine=engine
    )
    return


@app.cell
def _(engine, mo):
    _df = mo.sql(
        f"""
        SELECT * FROM raw._skipped_urls;
        """,
        engine=engine
    )
    return


if __name__ == "__main__":
    app.run()
