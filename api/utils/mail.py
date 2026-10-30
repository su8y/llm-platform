import os
import logging

import httpx



async def send_mail_by_dream_mailer(template_name, data, service_code=None):
    base_url = os.getenv("MAILER_API_URL")
    api_url = base_url + '/mailer/addMailQueue'
    try:
        async with httpx.AsyncClient() as client:
            await client.post(api_url, json={
                'serviceCode': service_code,
                'templateName': template_name,
                'data': data
            })
            return {"success": True, "error_message": None}
    except httpx.RequestError as e:
        message = str(e)
        logging.info(f"[utils.mail.send_mail_by_dream_mailer] 🔴 Unexpected error: {message}")
        return {"success": False, "error_message": message}
    except Exception as e:
        message = str(e)
        logging.info(f"[utils.mail.send_mail_by_dream_mailer] 🔴 Unexpected error: {message}")
        return {"success": False, "error_message": message}
    

async def send_find_password_mail_by_dream_mailer(template_name, data, service_code=None):
    base_url = os.getenv("MAILER_API_URL")
    api_url = base_url + '/mailer/addMailQueue'
    try:
        async with httpx.AsyncClient() as client:
            await client.post(api_url, json={
                'serviceCode': service_code,
                'templateName': template_name,
                'data': data
            })
            return {"success": True, "error_message": None}
    except httpx.RequestError as e:
        message = str(e)
        logging.info(f"[utils.mail.send_mail_by_dream_mailer] 🔴 Unexpected error: {message}")
        raise Exception(message)
    except Exception as e:
        message = str(e)
        logging.info(f"[utils.mail.send_mail_by_dream_mailer] 🔴 Unexpected error: {message}")
        raise Exception(message)