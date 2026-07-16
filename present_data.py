# /// script
# dependencies = [
#     "duckdb==1.5.4",
#     "marimo",
#     "polars==1.42.1",
#     "pyarrow==24.0.0",
#     "sqlglot==30.12.0",
# ]
# requires-python = ">=3.14"
# ///

import marimo

__generated_with = "0.21.1"
app = marimo.App(
    width="medium",
    auto_download=["html"],
    sql_output="lazy-polars",
)

with app.setup(hide_code=True):
    import marimo as mo


@app.cell(hide_code=True)
def _():
    _df = mo.sql(
        f"""
        install httpfs;
        load httpfs;
        create or replace secret (
            type 's3',
            key_id 'GKf045f7eff3cbcaa65fe60a73',
            secret '8488ca1797153334af962ef8a8ac17cb384481d43a51e936384b10e09322aea4',
            endpoint 's3.garage.balodis.id.lv',
            region 'garage',
            url_style 'path'
        );
        """,
        output=False
    )
    return


@app.cell(hide_code=True)
def _():
    session_type = mo.sql(
        f"""
        SELECT * FROM READ_PARQUET('s3://saeima-votes/dim.session_type.parquet');
        """,
        output=False
    )
    return (session_type,)


@app.cell(hide_code=True)
def _():
    loaded_urls = mo.sql(
        f"""
        SELECT * FROM READ_PARQUET('s3://saeima-votes/raw._loaded_urls.parquet');
        """,
        output=False
    )
    return


@app.cell(hide_code=True)
def _():
    dkp = mo.sql(
        f"""
        SELECT * FROM READ_PARQUET('s3://saeima-votes/raw.dkp.parquet');
        """,
        output=False
    )
    return (dkp,)


@app.cell(hide_code=True)
def _():
    dkp_items = mo.sql(
        f"""
        SELECT * FROM READ_PARQUET('s3://saeima-votes/raw.dkp_items.parquet');
        """,
        output=False
    )
    return (dkp_items,)


@app.cell(hide_code=True)
def _():
    debates = mo.sql(
        f"""
        SELECT * FROM READ_PARQUET('s3://saeima-votes/raw.debate.parquet');
        """,
        output=False
    )
    return (debates,)


@app.cell(hide_code=True)
def _():
    votes = mo.sql(
        f"""
        SELECT * FROM READ_PARQUET('s3://saeima-votes/raw.vote.parquet');
        """,
        output=False
    )
    return (votes,)


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Identificētie sesiju tipi
    """)
    return


@app.cell
def _(session_type):
    session_type.collect()
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Darba kārtības
    """)
    return


@app.cell
def _(dkp):
    dkp.collect()
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Darba kārtības punkti
    """)
    return


@app.cell
def _(dkp_items):
    dkp_items.collect()
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Balsošanas rezultāti
    """)
    return


@app.cell
def _(votes):
    votes.collect()
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Debašu informācija
    """)
    return


@app.cell
def _(debates):
    debates.collect()
    return


if __name__ == "__main__":
    app.run()
