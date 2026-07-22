import marimo

__generated_with = "0.23.14"
app = marimo.App()


@app.cell
def _():
    import duckdb

    _DATABASE_URL = "explore_saeima.db"
    engine = duckdb.connect(_DATABASE_URL, read_only=False)
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


@app.cell(hide_code=True)
def _(engine, mo):
    _df = mo.sql(
        f"""
        create view if not exists stg.dk as
        select
            SESSIONNAME::TEXT as session_name,
            strptime(SESSIONSTARTDATE, '%d.%m.%Y')::DATE as session_start_date,
            strptime(SESSIONENDDATE, '%d.%m.%Y')::DATE as session_end_date,
            [
                try_strptime(x, ['%d.%m.%Y %H:%M', '%d.%m.%Y']) FOR x IN string_split(CONTINUE_DATES, '#')
            ] as continue_dates,
            PARLAMENTNUMBER::UINT8 as parliament_number,
            DK_NUMBER::UINT8 as dk_number,
            strptime(DKDATE, '%d.%m.%Y')::DATE as dk_date,
            strptime(DKENDTIME, '%d.%m.%Y %H:%M') as dk_end_time,
            strptime(DKSTARTTIME, '%d.%m.%Y %H:%M') as dk_start_time,
            DKSTARTTIMETEXT as notes,
            SESSIONTYPE::UINT8 as session_type,
            STATUS::UINT8 as session_status,
            WORKSEQUENCEID as dk_id,
            MANUALTITLE as title
        from
            raw.dk;
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
            strptime(DATESUBMITED, '%d.%m.%Y')::DATE as date_submitted,
            case DEBATE_FLAG
                when 0 then FALSE
                when 1 then TRUE
            END as debate_flag,
            case HAS_DKP_CHILDS
                when 0 then FALSE
                when 1 then TRUE
            end as has_dkp_childs,
            DK_ID as dk_dk_id,
            DK_STATUS::UINT8 as session_status,
            DKP_ID as dkp_id,
            DKP_NUMBER::UINT8 as dkp_num,
            strptime(DKP_DKPSTARTTIME, '%H:%M')::TIME as dkp_start_time,
            strptime(DKP_DKPENDTIME, '%H:%M')::TIME as dkp_end_time,
            DKP_SECTION as section,
            DKP_SEQUENCE as sequence,
            DKP_SUBSECTION as subsection,
            DKP_TYPE::UINT8 as dkp_type,
            DKP_STATUS::UINT8 as dkp_status,
            LIVSDOCUMENTID as livs_id,
            MAIN_WORK_ITEM_ID as main_dkp_id,
            PARENTID as parent_dkp_id,
            PROPOSALCOUNT::UINT16 as proposal_count,
            READING::UINT8 as reading,
            RESULT as result,
            TITLE as dkp_title,
            VOTEMOTIVE as vote_motive,
            strptime(VOTESTARTTIME, '%H:%M')::TIME as vote_start_time,
            VOTERESULT_ABSTAIN::UINT8 as vote_result_abstain,
            VOTERESULT_AGAINST::UINT8 as vote_result_against,
            VOTERESULT_FOR::UINT8 as vote_result_for,
            VOTERESULT_REGISTERED::UINT8 as vote_result_registered,
            [x::UINT8 FOR x IN string_split(VOTE_TYPE, '#')] as vote_type,
            case RESPONSES
                when 0 then FALSE
                when 1 then TRUE
            END as responses,
            PASSINGTOCOMMISSION as nodots_komisijai,
            [x FOR x IN string_split(SPEAKER, '#')][:3] as zinotajs,
            DKP_INFO as notes
        from
            raw.dkp;
        """,
        engine=engine
    )
    return


@app.cell(hide_code=True)
def _(engine, mo):
    _df = mo.sql(
        f"""
        select distinct(SPEAKER) from raw.dkp where not ENDS_WITH(SPEAKER, '#');
        """,
        output=False,
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
            raw.vote;
        """,
        engine=engine
    )
    return


@app.cell
def _(engine, mo):
    _df = mo.sql(
        f"""
        create or replace view stg.vote as
        select
            dkp_id as dkp_dkp_id,
            dk_status::UINT8 as dk_status,
            case VOTEISHIDDEN
            	when 'O' then FALSE
            	when '1' then TRUE
            end as hidden,
            case VOTEISCANDIDATE
            	when '0' then FALSE
            	when '1' then TRUE
            end as vote_for_candidate,
            case VOTEWITHSIGNS
            	when '0' then FALSE
            	when '1' then TRUE
            end as vote_with_signs,
            [x FOR x in STR_SPLIT(NAME, '#')] as names,
            [x FOR x in STR_SPLIT(SURNAME, '#')] as surnames,
            [x FOR x in STR_SPLIT(FRACTION, '#')] as fractions,
            [x FOR x in STR_SPLIT(RESULT, '#')] as results,
            [x FOR x in STR_SPLIT(CANDIDATENAMES, '#')] as candidates,
            [x FOR x in STR_SPLIT(CANDIDATERESULT, '#')] as candidate_result
        from
            raw.vote;
        """,
        engine=engine
    )
    return


@app.cell
def _(engine, mo):
    _df = mo.sql(
        f"""
        SELECT * FROM stg.vote;
        """,
        engine=engine
    )
    return


@app.cell
def _(engine, mo):
    _df = mo.sql(
        f"""
        SELECT * FROM stg.dk;
        """,
        engine=engine
    )
    return


@app.cell
def _(engine, mo):
    _df = mo.sql(
        f"""
        SELECT * FROM stg.dkp;
        """,
        engine=engine
    )
    return


if __name__ == "__main__":
    app.run()
