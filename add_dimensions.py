import marimo

__generated_with = "0.23.14"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    from dotenv import load_dotenv
    import os

    load_dotenv('.env')
    return (os,)


@app.cell
def _():
    import duckdb

    _DATABASE_URL = "explore_saeima.db"
    engine = duckdb.connect(_DATABASE_URL, read_only=False)
    return (engine,)


@app.cell
def _(engine, mo):
    _df = mo.sql(
        f"""
        install httpfs;
        load httpfs;
        """,
        engine=engine
    )
    return


@app.cell
def _(engine, os):
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


@app.cell
def _(engine, mo):
    _df = mo.sql(
        f"""
        create schema if not exists dim;

        create table if not exists dim.session_type (session_type_id UINT8 PRIMARY key, name VARCHAR);

        insert
        or ignore into dim.session_type (session_type_id, NAME)
        values
            (1, 'Kārtējā'),
            (2, 'Ārkārtas sēde'),
            (3, 'Svinīgā sēde'),
            (5, 'Atbilžu sniegšana uz deputātu jautājumiem'),
            (6, 'Ārkārtas sesijas sēde');

        create table if not exists dim.session_status (session_status_id UINT8 PRIMARY key, name VARCHAR);

        insert
        or ignore into dim.session_status (session_status_id, NAME)
        values
            (6, 'Izskatīta'),
            (8, 'Atcelta');
        """,
        engine=engine
    )
    return


@app.cell
def _(engine, mo):
    _df = mo.sql(
        f"""
        copy (
            select
                *
            from
                dim.session_type
        ) to 's3://saeima-votes/dim.session_type.parquet' (format parquet, overwrite_or_ignore true);
        """,
        engine=engine
    )
    return


if __name__ == "__main__":
    app.run()
