const env = import.meta.env

let baseDomain = window.location.origin
if (env.VITE_APP_NODE_ENV === 'staging') {
  baseDomain = window.location.origin
} else if (env.VITE_APP_NODE_ENV === 'production') {
  baseDomain = window.location.origin
}

export const APP_DOMAIN = baseDomain

export const STORAGE_ITEM = {
  authToken: 'app-auth'
}

export const LOCALE_COOKIE = {
  name: 'app-locale',
  expires: 365,
  path: '/'
}

export const AUTH_COOKIE = {
  name: 'app-auth',
  expires: 1,
  path: '/'
}

export const ALERT_COOKIE = {
  name: 'app-alert',
  expires: 1,
  path: '/'
}

export const ID_REG_EXP = /^(?!.*[\sA-Z\u3130-\u318F\uAC00-\uD7A3])[a-z0-9._-]{5,20}$/
export const PW_REG_EXP = /^[^\s]{6,20}$/
export const EMAIL_REG_EXP = /^[\w._-]+@[^\u3131-\u3163\uac00-\ud7a3\s@]+\.[^\u3131-\u3163\uac00-\ud7a3\s]+(?<!\.)$/

// 내부 운영사 회사명 목록. 해당 회사는 답장 발송 확인을 생략한다
export const INTERNAL_COMPANY_NAMES = []
export const BEUSABE_EMAIL = ''
export const SUPPORT_EMAIL = import.meta.env.VITE_SUPPORT_EMAIL || ''
export const MCP_TITLE = 'AI Agent'
export const USE_MCP_ID_LIST = ['admin', 'hanmi_poc', 'schema_tag', 'mcp_journey']

export const STATUS = {
  all: 'all',
  needSolve: 'needSolve',
  reqExtraInfo: 'reqExtraInfo',
  confirming: 'confirming',
  editing: 'editing',
  checking: 'checking',
  editComplete: 'editComplete',
  notIssue: 'notIssue',
  completeAnswer: 'completeAnswer'
}

export const INCOMING_LIST = {
  none: 'none',
  chat: 'chat',
  mail: 'mail'
}

export const MONITORING_COLUMNS = [
  {
    title: MCP_TITLE,
    key: 'isMCP'
  },
  {
    title: 'chatTitle',
    key: 'chatTitle'
  },
  {
    title: 'status',
    key: 'issueStatus'
  },
  {
    title: 'chatDate',
    key: 'regDate'
  },
  {
    title: 'id',
    key: 'askerId'
  },
  {
    title: 'rating',
    key: 'rating'
  },
  {
    title: 'manager',
    key: 'managerId'
  }
]

export const REFERENCE_COLUMNS = [
  {
    title: 'checkbox',
    key: 'checkbox'
  },
  {
    title: 'isReference',
    key: 'is_on'
  },
  {
    title: 'depth1',
    key: 'depth1'
  },
  {
    title: 'depth2',
    key: 'depth2'
  },
  {
    title: 'depth3',
    key: 'depth3'
  },
  {
    title: 'title',
    key: 'title'
  },
  {
    title: 'createdDate',
    key: 'reg_date'
  },
  {
    title: 'author',
    key: 'author'
  },
  {
    title: 'citationCount',
    key: 'use_count'
  },
]

export const MEMBERS_COLUMNS = [
  {
    title:'status',
    key: 'status'
  },
  {
    title:'authority',
    key: 'authName'
  },
  {
    title:'department',
    key: 'department'
  },
  {
    title:'date',
    key: 'date'
  },
  {
    title:'id',
    key: 'userId'
  },
  {
    title: 'email',
    key: 'emailAddress'
  },
  {
    title: 'withdrawalOrResend',
    key: 'etc'
  }
]

export const PLAN_COLUMNS = [
  {
    title: 'planName',
    key: 'planName'
  },
  {
    title: 'usePeriod',
    key: 'usePeriod'
  },
  {
    title: 'questionCount',
    key: 'initCredit'
  },
  {
    title: 'useQuestionCount',
    key: 'useCredit'
  },
  // {
  //   title: 'paymentMethod',
  //   key: 'paymentType'
  // },
  // {
  //   title: 'paymentAmount',
  //   key: 'paymentPrice'
  // }
]
export const DRIVE_COLUMNS = [
  {
    title: 'fileName',
    key: 'fileName'
  },
  {
    title: 'fileType',
    key: 'fileType'
  },
  {
    title: 'fileSize',
    key: 'fileSize'
  },
  {
    title: 'status',
    key: 'status'
  },
  {
    title: 'regDate',
    key: 'regDate'
  }
]

export const PENPAL_LIST_COLUMNS = [
  {
    title: 'receivedAt',
    key: 'receivedAt'
  },
  {
    title: 'fromMail',
    key: 'fromMail'
  },
  {
    title: 'subject',
    key: 'subject'
  },
  {
    title: 'status',
    key: 'status'
  },
  {
    title: 'manager',
    key: 'manager'
  }
]


export const PENPAL_RAG_LIST_COLUMNS = [
  {
    title: 'sentAt',
    key: 'sentAt'
  },
  {
    title: 'toMail',
    key: 'toMail'
  },
  {
    title: 'subject',
    key: 'subject'
  },
  {
    title: 'manager',
    key: 'manager'
  }
]

export const PENPAL_STATUS = {
  all: "all",
  parsed: "parsed",
  answering: "answering",
  sent: "sent",
  close: "close",
  spam: "spam"
}

export const PENPAL_DETAIL_STATUS = {
  parsed: "parsed",
  answering: "answering",
  sent: "sent",
  close: "close",
  spam: "spam"
}

export const DRIVE_STATUS = {
  0: 'failed',
  1: 'pending',
  2: 'success',
  3: 'analyzing',
  4: 'finished',
  5: 'unparsed'
}

export const REFERENCE_TYPE = {
  all: 'all',
  reference: 'onReference',
  notReference: 'offReference'
}

export const PAGE_OPTIONS = [10, 20, 50, 100]

export const SEARCH_AUTHORITY = {
  all: 'all',
  manager: 'Manager',
  Viewer: 'Viewer'
}

export const AUTHORITY = {
  master: 'Master',
  manager: 'Manager',
  Viewer: 'Viewer'
}

export const MEMBERS_STATUS = {
  all: 'all',
  waiting: 'waiting',
  complete: 'complete',
  expired: 'expired',
  false: 'false'
}

export const HTTP_CODES = {
  DUPLICATED: {
    ID: 9000,
    EMAIL: 9001,
    COMPANY: 9002,
  },
  INVALID_EMAIL: 9003,
  HAS_THREAD: 9005,
  SERVER: 500,
  BAD_REQUEST: 400,
  USE_CATEGORY: 998,
  NOT_REGISTERED_ID: 402,
  NOT_REGISTERED_PASSWORD: 403,
  NOT_CERTIFIED_EMAIL: 405,
  SUCCESS: 200
}

export const WARNING_TYPE = {
  AUTHORITY: 'authority',
  SECESSION: 'secession',
  REFERENCE_DELETE: 'referenceDelete',
  CERTIFICATION_EMAIL: 'cetificationEmail',
  EXPIRATION_INVITATION: 'invitation',
  CATEGORY_DELETE: 'categoryDelete',
  CATEGORY_USE_REFERENCE: 'categoryUseReference',
  DUPLICATED_EMAIL: 'duplicatedEmail',
  INVALID_EMAIL: 'invalidEmail',
  DUPLICATED_RE_INVITE: 'reInvite',
  EMPTY_DUPLICATED_CATEGORY: 'emptyCategory',
  EDIT_CATEGORY: 'editCategory',
  CHILD_CATEGORY_EXISTENCE: 'childCategoryExistence',
  FILE_UPLOAD_ERROR: 'fileUploadError',
  PARSER_CREDIT_ERROR: 'parserCreditError',
  CATEGORY_SAVE: 'categorySave',
  PLAN_CANCEL: 'planCancel',
  DELETE: 'delete',
  UPDATE_PDF_FILE: 'updatePdfFile',
  UPDATE_PDF_CANCEL: 'updatePdfCancel',
  DELETE_PDF_FILE: 'deletePdfFile',
  REQUIRED_COMMENT: 'requiredComment',
  SEND_CONFIRM: 'sendConfirm',
  PASSWORD_LINK_EXPIRED: 'passwordLinkExpired',
  ATTACHMENT_ERROR: 'attachmentError',
  SEND_MAIL_ERROR: 'sendMailError',
  HAS_THREAD: 'hasThread',
  EMAIL_COUNT_ERROR: 'emailCountError',
  FAILED_SEND_MAIL: 'failedSendMail',
}

export const SUCCESS_TYPE = {
  AUTHENTICATION_EMAIL: 'authenticationEmail',
  TEMPORARY_SAVE: 'temporarySave',
  SEND_MAIL: 'sendMail',
  CHANGE_PASSWORD: 'changePassword'
}

export const SEND_MAIL_TYPE = {
  SEND_INVITE: 'sendInvite',
  SEND_REGISTER: 'sendRegister',
  SEND_RESET_PASSWORD: 'sendResetPassword',
  SEND_AI_EMAIL: 'sendAiEmail',
}

export const PLAN_LIST = {
  all: 'all',
  pilot: 'Pilot',
  basic: 'Basic',
  premium: 'Premium',
  pro: 'Pro',
  questionPackage: 'QuestionPackage',
  custom: 'Custom'
}

export const PLAN_NUMBER = [
  {
    id: 3,
    title: 'Pilot'
  },
  {
    id: 4,
    title: 'Basic'
  },
  {
    id: 5,
    title: 'Premium'
  },
  {
    id: 6,
    title: 'Pro'
  },
  {
    id: 7,
    title: 'QuestionPackage'
  },
]

export const LANGUAGE_LIST = [
  { code: 'ko', name: '한국어' },
  { code: 'en', name: 'English' },
  { code: 'ja', name: '日本語' }
]

export const I18N_CUSTOM_MAPPING =  {
  'mainStart': [
    'start',
    'register',
    'support'
  ],
  'mainOption': [
    'sass',
    'premise',
    'hybrid'
  ],
  'mainSuccess': [
    'electron',
    'finance',
    'it'
  ],
  'whyHappen': [
    'mon',
    'tue',
    'wed',
    'thu'
  ],
  'whyWrite': [
    'post',
    'tech',
    'search'
  ],
  'whyWord': [
    'write',
    'learning',
    'dialog',
    'source'
  ],
  'whyEnterprise': [
      '',
    'yellow',
    'green',
    'purple',
  ],
  'kmsValue': [
    'record',
    'auto',
    'avatar',
  ],
  'kmsConjugation': [
    'hr',
    'it',
    'business',
    'legal'
  ],
  'kmsEffect': [
    '70%',
    '85%',
    '90%',
    '100%'
  ],
  'csValue': [
    'reg',
    'search',
    'connect'
  ],
  'fileValue': [
    'upload',
    'analysis',
    'structure',
    'conjugation'
  ]
}

export const ORGANIZATION_CTG_LIST = [
  {
    id: 'all',
    value: '전체'
  },
  {
    id: 'policy',
    value: '정책/행정'
  },
  {
    id: 'farming',
    value: '농축수산/환경'
  },
  {
    id: 'traffic',
    value: '교통/인프라'
  },
  {
    id: 'welfare',
    value: '복지/경제'
  },
  {
    id: 'culture',
    value: '문화/관광'
  },
  {
    id: 'promotion',
    value: '대외협력/홍보'
  },
]


