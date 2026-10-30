import { unified } from 'unified'

// markdown to html
import remarkGfm from 'remark-gfm'
import markdown from 'remark-parse'
import remark2rehype from 'remark-rehype'
import html from 'rehype-stringify'
import rehypePrismPlus from 'rehype-prism-plus'
import rehypeExternalLinks from 'rehype-external-links'

// html to markdown
import rehypeParse from 'rehype-parse'
import rehype2remark from 'rehype-remark'
import remarkStringify from 'remark-stringify'

import { visit } from 'unist-util-visit'

const regex = /&(nbsp|amp|lt|gt|quot|#39);/g
const chars = {
  '&nbsp;': ' ',
  '&amp;': '&',
  '&lt;': '<',
  '&gt;': '>',
  '&quot;': '"',
  '&#39;': "'"
}

export const unescape = (str) => {
  if (regex.test(str)) {
    return str.replace(regex, (matched) => chars[matched] || matched)
  }

  return str
}

export const applyAdditionalFormatting = () => {
  return (tree) => {
    visit(tree, 'element', (node) => {
      // add data-language attribute
      if (node.tagName === 'pre' &&  node.children[0]) {
        const codeClassList = node.children[0].properties.className || []
        const langClass = codeClassList.find((cls) =>
            cls.startsWith('language-')
        )

        if (langClass) {
          const preClassList = node.properties.className || []
          if (!preClassList.includes(langClass)) {
            preClassList.push(langClass)
            node.properties.className = preClassList;
          }

          const language = langClass.replace('language-', '')
          node.properties['data-language'] = language
        }
      }

      if (node.tagName === 'li') {
        node.properties.style = 'white-space: normal; line-height: 2;'
      }

      if (node.tagName === 'img') {
        node.properties.style = 'max-width: 80%; height: auto; padding: 20px 0;'
      }
    })
  }
}

export const convertMarkdownToHtml = (markDownText) => {
  if (!markDownText) return '';

  // 인용문 직접 처리 (> 로 시작하는 줄)
  const processQuotes = (text) => {
    const lines = text.split('\n');
    let inQuote = false;
    let result = '';
    let quoteContent = '';

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      if (line.trim().startsWith('>')) {
        // 인용문 시작 또는 계속
        inQuote = true;
        quoteContent = '';
        // > 제거하고 내용만 추출
        quoteContent += line.replace(/^>\s*/, '') + '\n'
      } else {
        // 인용문이 끝남
        if (inQuote) {
          result += `<blockquote><p>${quoteContent}</p></blockquote>\n`;
          inQuote = false;
        }
        result += line + '\n';
      }
    }

    // 마지막 인용문 처리
    if (inQuote) {
      result += `<blockquote><p>${quoteContent}</p></blockquote>\n`;
    }

    return result;
  };

  // 백슬래시 제거
  const cleanedText = markDownText.replace(/\\/g, '');

  // 인용문 사전 처리
  const processedText = processQuotes(cleanedText);

    // 나머지 마크다운 처리
    const result = unified()
      .use(markdown)
      .use(remarkGfm, { singleTilde: false })
      .use(remark2rehype, { allowDangerousHtml: true })
      .use(rehypePrismPlus)
      .use(rehypeExternalLinks)
      .use(html, { allowDangerousHtml: true })
      .processSync(processedText);

    return result.value;

  }

export const convertHtmlToMarkdown = async (htmlText) => {
  const result = await unified()
    .use(rehypeParse, { fragment: true })
    .use(rehype2remark)
    .use(remarkGfm, { singleTilde: false })
    .use(remarkStringify, {
      fences: true,
      bullet: '-',
    })
    .process(htmlText)

  return result.value
}


export const formatDate = (dateStr, type = null) => {
  const date = new Date(dateStr)
  const TIME_ZONE = 9 * 60 * 60 * 1000 // 9시간

  if (Object.prototype.toString.call(date) !== '[object Date]' || isNaN(date)) {
    return ''
  }

  if (type === 'num') {
    return (
      date
        .toLocaleDateString('ko-KR', {year: 'numeric', month: '2-digit', day: '2-digit'})
        .replace(/[^0-9]/g, '') +
      ' ' +
      date
        .toLocaleTimeString('ko-KR', {
          hour12: false,
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        })
        .replace(/[^0-9]/g, '')
    )
  }
  if (type === 'yyyy-mm-dd') {
    return new Date(date.getTime() + TIME_ZONE).toISOString().replace('T', ' ').slice(0, -5)
  }
}
