import marimo

__generated_with = "0.23.14"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


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


if __name__ == "__main__":
    app.run()
