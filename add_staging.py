import marimo

__generated_with = "0.23.14"
app = marimo.App()


@app.cell
def _():
    import duckdb

    DATABASE_URL = "explore_saeima.db"
    engine = duckdb.connect(DATABASE_URL, read_only=False)
    return (engine,)


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(engine, mo):
    _df = mo.sql(
        f"""
        create schema if not exists stg;
        """,
        engine=engine
    )
    return


@app.cell
def _(engine, mo):
    _df = mo.sql(
        f"""
        SELECT
            *
        FROM
            raw.dkp_items;
        """,
        engine=engine
    )
    return


@app.cell(hide_code=True)
def _(engine, mo):
    _df = mo.sql(
        f"""
        create view if not exists stg.dkp as
        select
            SESSIONNAME::TEXT as session_name,
            strptime(SESSIONSTARTDATE, '%d.%m.%Y')::DATE as session_start_date,
            strptime(SESSIONENDDATE, '%d.%m.%Y')::DATE as session_end_date,
            [
                try_strptime(x, ['%d.%m.%Y %H:%M', '%d.%m.%Y']) FOR x IN string_split(CONTINUE_DATES, '#')
            ] as continue_dates,
            PARLAMENTNUMBER::UINT8 as parliament_number,
            DK_NUMBER::UINT8 as agenda_number,
            strptime(DKDATE, '%d.%m.%Y')::DATE as agenda_date,
            strptime(DKENDTIME, '%d.%m.%Y %H:%M') as agenda_end_time,
            strptime(DKSTARTTIME, '%d.%m.%Y %H:%M') as agenda_start_time,
            DKSTARTTIMETEXT as notes,
            SESSIONTYPE::UINT8 as session_type,
            WORKSEQUENCEID as dkp_id,
            MANUALTITLE as title
        from
            raw.dkp;
        """,
        engine=engine
    )
    return


@app.cell
def _(engine, mo):
    _df = mo.sql(
        f"""
        -- create view if not exists stg.dkp_items as
        create or replace view stg.dkp_items as
        select
            *
        from
            raw.dkp_items;
        """,
        engine=engine
    )
    return


@app.cell
def _(engine, mo):
    df = mo.sql(
        f"""
        SELECT * FROM stg.dkp_items;
        """,
        engine=engine
    )
    return


if __name__ == "__main__":
    app.run()
