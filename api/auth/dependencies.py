import ast
import logging

from fastapi import Depends
from jose import jwt, ExpiredSignatureError, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from models import get_db
from queries.user_info import UserInfoQuery
from utils.error import DBError, TokenError
from auth import *



def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        if not token:
            logging.info(f"[auth.dependencies.get_current_user] Invalid token: {token}")
            raise TokenError("Invalid token")
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") == "access":
            identity = payload.get("sub")
            if not identity:
                logging.info(f"[auth.dependencies.get_current_user] Invalid token: {token}")
                raise TokenError("Invalid token")
            return identity
        else:
            logging.info(f"[auth.dependencies.get_current_user] Invalid token: {token}")
            raise TokenError("Invalid token")    
    
    except ExpiredSignatureError as e:
        logging.info(f"[auth.dependencies.get_current_user] ExpiredSignatureError: {e}")
        raise TokenError(e)
    except JWTError as e:
        logging.info(f"[auth.dependencies.get_current_user] JWTError: {e}")
        raise TokenError(e)
    except Exception as e:
        logging.info(f"[auth.dependencies.get_current_user] Exception: {e}")
        raise TokenError("Invalid token")


async def get_user_info(
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    try:
        if isinstance(current_user, str):
            current_user = ast.literal_eval(current_user)
        
        user_id = current_user.get('user_id')
        session_key = current_user.get("session_key")

        user_info_query = UserInfoQuery()
        user_info = await user_info_query.get_user_info_from_token_raw(db=db, user_id=user_id)
        user_info['session_key'] = session_key
        
        return user_info
    
    except DBError as e:
        logging.info(f"[auth.dependencies.get_user_info] DBError: {e}")
        raise TokenError("Invalid token")
    except ExpiredSignatureError as e:
        logging.info(f"[auth.dependencies.get_user_info] ExpiredSignatureError: {e}")
        raise TokenError(e)
    except JWTError as e:
        logging.info(f"[auth.dependencies.get_user_info] JWTError: {e}")
        raise TokenError("Invalid token")
    except TokenError as e:
        logging.info(f"[auth.dependencies.get_user_info] TokenError: {e}")
        raise TokenError("Invalid token")
    except Exception as e:
        logging.info(f"[auth.dependencies.get_user_info] Exception: {e}")
        raise TokenError("Invalid token")


# 액세스 토큰 선택적 (일부 정보만 필요한 라우트용)
def get_optional_user(token: str = Depends(oauth2_scheme)):
    try:
        if not token:
            result = None
    
        else:    
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") == "access":
                identity = payload.get("sub")
                result = identity
            else:
                result = None
    
        return result 
    
    except TokenError as e:
        logging.info(f"[auth.dependencies.get_optional_user] TokenError: {e}")
        raise TokenError("Invalid token")
    except ExpiredSignatureError as e:
        logging.info(f"[auth.dependencies.get_optional_user] ExpiredSignatureError: {e}")
        raise TokenError(e)
    except JWTError as e:
        logging.info(f"[auth.dependencies.get_optional_user] JWTError: {e}")
        raise TokenError("Invalid token")
    except Exception as e:
        logging.info(f"[auth.dependencies.get_optional_user] Exception: {e}")
        raise TokenError("Invalid token")
    

async def get_user_info_for_playground(
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_optional_user)
):
    try:
        if current_user is None:
            return None

        if isinstance(current_user, str):
            current_user = ast.literal_eval(current_user)
        
        user_id = current_user.get('user_id')
        session_key = current_user.get("session_key")

        user_info_query = UserInfoQuery()
        user_info = await user_info_query.get_user_info_from_token_raw(db=db, user_id=user_id)
        user_info['session_key'] = session_key
        
        return user_info
    
    except DBError as e:
        logging.info(f"[auth.dependencies.get_user_info] DBError: {e}")
        raise TokenError("Invalid token")
    except ExpiredSignatureError as e:
        logging.info(f"[auth.dependencies.get_user_info] ExpiredSignatureError: {e}")
        raise TokenError(e)
    except JWTError as e:
        logging.info(f"[auth.dependencies.get_user_info] JWTError: {e}")
        raise TokenError("Invalid token")
    except TokenError as e:
        logging.info(f"[auth.dependencies.get_user_info] TokenError: {e}")
        raise TokenError("Invalid token")
    except Exception as e:
        logging.info(f"[auth.dependencies.get_user_info] Exception: {e}")
        raise TokenError("Invalid token")


# 리프레시 토큰 필수 (토큰 갱신용)
def get_refresh_user(token: str = Depends(oauth2_scheme)):
    try:
        if not token:
            result = None
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") == "refresh":
            identity = payload.get("sub")
            result = identity
        else:
            result = None
    
        return result 
    
    except ExpiredSignatureError as e:
        logging.info(f"[auth.dependencies.get_optional_user] 🔴 {e}")
        raise TokenError(e)
    except JWTError as e:
        logging.info(f"[auth.dependencies.get_optional_user] 🔴 {e}")
        raise TokenError(e)
    except TokenError as e:
        logging.info(f"[auth.dependencies.get_refresh_user] TokenError: {e}")
        raise TokenError("Invalid token")
    except Exception as e:
        logging.info(f"[auth.dependencies.get_refresh_user] Exception: {e}")
        raise TokenError("Invalid token")