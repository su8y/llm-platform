from fastapi import Form
from pydantic import BaseModel, Field
from typing import Optional
from utils.constants import *



class InboxListPayload(BaseModel):
    page: int = Field(..., alias="page", description="Page Number")
    per_page: int = Field(..., alias="perPage", description="Size per Page")
    subject: Optional[str] = Field(None, alias="subject")
    start_date: Optional[str] = Field(None, alias="startDate")
    end_date: Optional[str] = Field(None, alias="endDate")
    from_: Optional[str] = Field(None, alias="from")
    manager: Optional[str] = Field(None, alias="manager")
    status: Optional[str] = Field(None, alias="status")


class getInboxPayload(BaseModel):
    id: int = Field(..., alias="id", description="Email ID")


class UpdateCompanyPayload(BaseModel):
    id: int = Field(..., alias="id", description="Email ID")
    company: str = Field(..., alias="company", description="Company Name which user want to change")


class GetInboxHistoryPayload(BaseModel):
    id: int = Field(..., alias="id", description="Email ID")


class SetManagerPayload(BaseModel):
    id: int = Field(..., alias="id", description="Email ID")
    manager_id: str = Field(..., alias="managerId", description="manager account")

class GetStatusQueryParams(BaseModel):
    id: Optional[str] = Field(None, alias="id", description="Email ID")
    current_status: Optional[str] = Field(None, alias="currentStatus", description="current email status")


class ChangeStatusPayload(BaseModel):
    id: int = Field(..., alias="id", description="Email ID")
    status: str = Field(..., alias="status", description="status which is selected")

class UpdateReceiveCommentPayload(BaseModel):
    id: int = Field(..., alias="id", description="Email ID")
    comment: Optional[str] = Field(..., alias="comment", description="comment which manager write for updating")


class inboxFileDownload(BaseModel):
    s3Key : str = Field(..., alias="s3Key", description="S3Key")


class InitAnswerPayload(BaseModel):
    id: int = Field(..., alias="id", description="Email ID")


class CreateAnswerPayload(BaseModel):
    id: int = Field(..., alias="id", description="Email ID")
    service: Optional[str] = Field(SERVICE_VOC_STAGING, alias="service", description="Service")
    vendor: Optional[str] = Field("openai", alias="vendor", description="Vendor")
    model: Optional[str] = Field("o3-mini", alias="model", description="Model")
    question: Optional[str] = Field("", alias="question", description="Question")


class GetSendInfoPayload(BaseModel):
    id: int = Field(..., alias="id", description="Email ID")


class SaveSendInfoPayload(BaseModel):
    id: int = Field(..., alias="id", description="Email ID")
    from_mail: Optional[str] = Field(None, alias="fromMail", description="Email Address of Sender")
    from_name: Optional[str] = Field(None, alias="fromName", description="Name of Sender")
    to_mail: Optional[list[str]] = Field([], alias="toMail", description="Email Address of Receiver")
    to_name: Optional[list[str]] = Field([], alias="toName", description="Name of Receiver")
    cc_mail: Optional[list[str]] = Field([], alias="ccMail", description="Email Address of CarbonCopy")
    cc_name: Optional[list[str]] = Field([], alias="ccName", description="Name of CarbonCopy")
    bcc_mail: Optional[list[str]] = Field([], alias="bccMail", description="Email Address of BehindCarbonCopy")
    bcc_name: Optional[list[str]] = Field([], alias="bccName", description="Name of BehindCarbonCopy")
    subject: Optional[str] = Field(None, alias="subject", description="Subject")
    answering_content: Optional[str] = Field(None, alias="answeringContent", description="Content")
    comment: str = Field(..., alias="comment", description="Comment")
    attachments: Optional[list[dict]] = Field(None, alias="attachments", description="Attachments")


class CheckHasThreadPayload(BaseModel):
    id: int = Field(..., alias="id", description="Email ID")


class SendEmailPayload(BaseModel):
    id: int = Field(..., alias="id", description="Email ID")
    email_html: str = Field(..., alias="emailHtml", description="Thread: Email HTML Content")
    image_info: Optional[list] = Field(None, alias="imageInfo", description="add New-Image from sender")


class DeleteSentEmailPayload(BaseModel):
    id: int | list[int] = Field(..., alias="id", description="EmailSendHistoryId")


class GetSESBouncePayload(BaseModel):
    notificationType: str = Field(..., alias="notificationType")
    bounce: dict = Field(..., alias="bounce")
    mail: dict = Field(..., alias="mail")


class SendEmailFormData:
    def __init__(
        self,
        id: Optional[str] = Form(None, alias="id", description="Email ID"),
        reply_subject: str = Form(..., alias="replySubject", description="Reply Subject"),
        reply_to: list[str] | str = Form(..., alias="replyTo", description="fromMail"),
        reply_to_name: Optional[list[str] | str] = Form(None, alias="replyToName", description="fromName"),
        reply_cc: Optional[list[str] | str] = Form(None, alias="replyCc", description="ccMail"),
        reply_cc_name: Optional[list[str] | str] = Form(None, alias="replyCcName", description="ccName"),
        reply_from: list[str] | str = Form(..., alias="replyFrom", description="toMail"),
        reply_from_name: list[str] | str = Form(..., alias="replyFromName", description="toName") ,
        keyword: Optional[str] = Form(None, alias="keyword", description="keyword"),
        template_name: str = Form(..., alias="templateName", description="Template Name"),
        email_html: str = Form(..., alias="emailHtml", description="Thread: Email HTML Content"),
        message_id: str = Form(..., alias="messageId", description="Message ID"),
        references: list[str] = Form(..., alias="references", description="references"),
        content: str = Form(..., alias="content", description="content"),
        manager_id: str = Form(..., alias="managerId", description="Manager ID"),
        comments: Optional[str] = Form(None, alias="comments", description="Comments"),
        company: Optional[str] = Form(None, alias="company", description="company"),
        received_at: str = Form(..., alias="receivedAt", description="receivedAt"),
        image_info: Optional[str] = Form(None, alias="imageInfo", description="add New-Image from sender")
    ):
        self.id = id
        self.reply_subject = reply_subject
        self.reply_to = reply_to
        self.reply_to_name = reply_to_name
        self.reply_cc = reply_cc
        self.reply_cc_name = reply_cc_name
        self.reply_from = reply_from
        self.reply_from_name = reply_from_name
        self.keyword = keyword
        self.template_name = template_name
        self.email_html = email_html
        self.message_id = message_id
        self.references = references
        self.content = content
        self.manager_id = manager_id
        self.comments = comments
        self.company = company
        self.received_at = received_at
        self.image_info = image_info


class UploadBase64Payload(BaseModel):
    image: list = Field(..., alias="image")


class GetDashboardChartPayload(BaseModel):
    start_date: str = Form(..., alias="startDate", description="start date of period which user select")
    end_date: str = Form(..., alias="endDate", description="end date of period which user select")
    timezone: Optional[str] = Form("Asia/Seoul", alias="timezone", description="client timezone. default value is Seoul")


class GetDashboardLinePayload(BaseModel):
    start_date: str = Form(..., alias="startDate", description="start date of period which user select")
    end_date: str = Form(..., alias="endDate", description="end date of period which user select")
    timezone: Optional[str] = Form("Asia/Seoul", alias="timezone", description="client timezone. default value is Seoul")


class GetDashboardManagerCntPayload(BaseModel):
    start_date: str = Form(..., alias="startDate", description="start date of period which user select")
    end_date: str = Form(..., alias="endDate", description="end date of period which user select")
