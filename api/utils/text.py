import re
import base64
import html2text
import logging
from bs4 import BeautifulSoup


def html_to_markdown(html_str):
    h = html2text.HTML2Text()
    # set options
    h.ignore_links = False
    h.ignore_images = False
    h.ignore_emphasis = False
    h.body_width = 0 # 줄바꿈
    h.single_line_break = True

    markdown = h.handle(html_str)
    return markdown


def html_to_text(html_str):
    soup = BeautifulSoup(html_str, "html.parser")
    return soup.get_text()


def get_clean_text(text, keep_html_tags=True, allowed_html_tags=None):
    """
    입력된 텍스트를 전처리하여 노이즈를 제거하고 필요한 HTML 태그를 유지합니다.

    Example:
        sample_text = '''
        <h1>안녕하세요!</h1>
        <p>이것은 <b>테스트</b> 문장입니다. 방문해 주세요: <a href="https://example.com">예시 사이트</a></p>
        '''

        # 1. 필요한 HTML 태그를 유지하는 경우
        processed_text = process_text(sample_text, keep_html_tags=True)
        print("HTML 태그 유지:")
        print(processed_text)
        >>>
            HTML 태그 유지:
            <h1>안녕하세요</h1> <p>이것은 <b>테스트</b> 문장입니다 방문해 주세요 예시 사이트</p>

        # 2. 모든 HTML 태그를 제거하는 경우
        processed_text_no_tags = process_text(sample_text, keep_html_tags=False)
        print("HTML 태그 제거:")
        print(processed_text_no_tags)
        >>>
            HTML 태그 제거:
            안녕하세요 이것은 테스트 문장입니다 방문해 주세요 예시 사이트

    :param text: 전처리할 원본 텍스트
    :param keep_html_tags: True일 경우 지정된 태그를 유지하고, False일 경우 모든 태그를 제거합니다.
    :param allowed_html_tags: 유지할 태그의 리스트. None일 경우 기본 태그 리스트를 사용합니다.
    :return: 전처리된 텍스트
    """
    try:
        # 1. HTML 태그 처리
        soup = BeautifulSoup(text, "html.parser")

        if keep_html_tags:
            if allowed_html_tags is None:
                # 기본적으로 유지할 태그 리스트
                allowed_html_tags = ['p', 'b', 'strong', 'em', 'h1', 'h2', 'h3', 'ul', 'li', 'ol']
            for tag in soup.find_all():
                if tag.name not in allowed_html_tags:
                    tag.unwrap()
                else:
                    # 태그 속성 제거
                    tag.attrs = {}
            text = str(soup)
        else:
            # 모든 태그 제거하고 텍스트만 추출
            text = soup.get_text(separator=' ')

        # 2. 불필요한 공백 제거
        text = ' '.join(text.split())

        return text

    except Exception as e:
        logging.error(f"[module.LLM.helper.get_clean_text] Exception: {e}")
        raise e


def remove_base64_images(text: str) -> str:
    text = re.sub(r'data:image/[^;]+;base64,[A-Za-z0-9+/]+=*', '[IMAGE_REMOVED]', text)
    text = re.sub(r'(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{200,}={0,2}(?![A-Za-z0-9+/])', '[LARGE_DATA_REMOVED]', text)
    return text