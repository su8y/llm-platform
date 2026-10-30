import logging

from sqlalchemy.ext.asyncio import AsyncSession

from queries.prompt_history import PromptHistoryQuery
from queries.company_info import CompanyInfoQuery
from payload.prompt import *
from domain.prompt import *
from utils.error import *
from utils.date import *

def helper_insert_prompt_make_domain_data(payload:insertPromptPayload, user_info:dict):
    try:
        return insertPromptDomain(
            user_id=user_info['user_id'],
            company_key=user_info['company_key'],
            prompt_name=payload.prompt_name,
            prompt=payload.prompt,
            comment=payload.comment,
            reg_date=get_utc_now()
        )
    except Exception as e:
        logging.error(f"[helper.prompt.helper_insert_prompt_make_domain_data] Exception: {e}")
        raise e

async def helper_insert_prompt(db:AsyncSession, prompt_history_query:PromptHistoryQuery, domain_data:insertPromptDomain):
    try:
        data = await prompt_history_query.create_prompt(
            db=db,
            domain_data=domain_data
        )
        return data
    except DBError as e:
        logging.error(f"[helper.prompt.helper_insert_prompt] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.prompt.helper_insert_prompt] Exception: {e}")
        raise e


async def helper_get_greetings(db:AsyncSession, company_info_query:CompanyInfoQuery, domain_data:getGreetingsDomain):
    try:
        domain_data.greetings = await company_info_query.get_greetings(db, domain_data)
        if not domain_data.greetings:
            domain_data.greetings = INIT_GREETING_KO
    except DBError as e:
        logging.error(f"[helper.prompt.helper_get_greetings] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.prompt.helper_get_greetings] Exception: {e}")
        raise e
    

async def helper_update_greetings(db:AsyncSession, company_info_query:CompanyInfoQuery, domain_data:updateGreetingsDomain):
    try:
        await company_info_query.update_greetings(db, domain_data)
    except DBError as e:
        logging.error(f"[helper.prompt.helper_update_greetings] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.prompt.helper_update_greetings] Exception: {e}")
        raise DataError(e)