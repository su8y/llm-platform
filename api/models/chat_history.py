from uuid import uuid4

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship

from . import Base



class ChatHistory(Base):
    __tablename__ = "chat_history"
    #Columns
    id = Column(String(40), primary_key=True, default=str(uuid4).replace("-", ""))
    session_key = Column(String(40), nullable=False)
    company_key = Column(String(40), ForeignKey("company_info.company_key"))
    role = Column(String(5), nullable=False)
    message = Column(Text, nullable=False)
    reg_date = Column(DateTime)
    model = Column(String(100))
    token = Column(Integer)
    rating = Column(Integer, nullable=True)
    prompt_id = Column(Integer, ForeignKey("prompt_history.id"))
    refer_id = Column(String(1000))
    parser_id = Column(String(1000))
    sitemap_id = Column(String(1000))
    email_id = Column(String(1000))
    question_id = Column(String(40), ForeignKey("chat_history.id"), nullable=True)
    solved = Column(Boolean, default=False)
    issue_status = Column(String(20), default="needSolve")
    asker_id = Column(String(30), nullable=True)
    asker_name = Column(String(30), nullable=True)
    asker_email_address = Column(String(50), nullable=True)
    asker_company = Column(String(30), nullable=True)
    memo = Column(Text, nullable=True)
    memo_updated_date = Column(DateTime, nullable=True)
    manager_id = Column(String(30), ForeignKey("user_info.user_id"), nullable=True, default='')
    assessor_id = Column(String(30), ForeignKey("user_info.user_id"), nullable=True, default='')
    elapsed_info = Column(String(1000), nullable=True)
    mcp_tools = Column(String(1000), nullable=True)
    is_mcp = Column(Boolean, server_default="0")
    init_date = Column(DateTime)


    # 관계설정
    company = relationship("CompanyInfo", backref="chat")
    manager = relationship("UserInfo", foreign_keys=[manager_id], backref="manager_chat")
    assessor = relationship("UserInfo", foreign_keys=[assessor_id], backref="assessor_chat")
    prompt = relationship("PromptHistory", backref="chat")
    

    @property
    def serialize(self):
        return {
            "id": str(self.id),
            "session_key": self.session_key,
            "company_key": self.company_key,
            "role": self.role,
            "message": self.message,
            "reg_date": self.reg_date,
            "model": self.model,
            "token": self.token,
            "rating": self.rating,
            "prompt_id": self.prompt_id,
            "refer_id": self.refer_id,
            "question_id": self.question_id,
            "solved": self.solved,
            "issue_status": self.issue_status,
            "asker_id": self.asker_id,
            "asker_name": self.asker_name,
            "asker_email_address": self.asker_email_address,
            "asker_company": self.asker_company,
            "memo": self.memo,
            "memo_updated_date": self.memo_updated_date,
            "manager_id": self.manager_id,
            "assessor_id": self.assessor_id
        }