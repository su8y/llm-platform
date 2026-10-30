import { fileUploadBase64 } from "@/api/penpal.js";

// cid -> s3
export const convertCidToS3 = (imageInfoArray, content) => {
  if (!imageInfoArray || !Array.isArray(imageInfoArray) || !content) {
    return content
  }

  let processedContent = content
  const reversedImageInfo = [...imageInfoArray].reverse()
  const dom = document.createElement('div')
  dom.innerHTML = processedContent
  const imgList = dom.querySelectorAll('img')

  for (const imgElem of imgList) {
    const src = imgElem.getAttribute('src')

    if (src && src.includes('cid:')) {
      const cidValue = src.replace('cid:', '')

      const matchingImage = reversedImageInfo.find(imageInfo => imageInfo.cid === cidValue)

      if (matchingImage && matchingImage.imageURL) {
        processedContent = processedContent.replace(src, matchingImage.imageURL)
      }
    }
  }

  return processedContent
}

// s3 -> cid
export const convertS3ToCid = (imageInfoArray, content) => {
  if (!imageInfoArray || !Array.isArray(imageInfoArray) || !content) {
    return content
  }

  let processedContent = content
  const dom = document.createElement('div')
  dom.innerHTML = processedContent
  const imgList = dom.querySelectorAll('img')

  for (const imgElem of imgList) {
    const src = imgElem.getAttribute('src')

    if (src) {
      const matchingImage = imageInfoArray.find(imageInfo => imageInfo.imageURL === src)

      if (matchingImage && matchingImage.cid) {
        const cid = `cid:${matchingImage.cid}`
        processedContent = processedContent.replace(src, cid)
      }
    }
  }

  return processedContent

}


// base64 -> cid
export const convertBase64ToCid = async (content, editorElement = null) => {
  try {
    const imageList = []

    const imgList = editorElement.querySelectorAll('img')
    for (const imgElem of imgList) {
      const imageSrc = imgElem.getAttribute('src')
      if (imageSrc && imageSrc.includes('data:image/') && imageSrc.includes('base64')) {
        imageList.push(imageSrc)
      }
    }

    if (imageList.length === 0) {
      return { content, convertImageList: '' }
    }

    const response = await fileUploadBase64({ image: imageList })

    if (!response || response.length === 0) {
      return { content, convertImageList: '' }
    }

    let processedContent = content
    const convertImageList = JSON.stringify(response)

    for (let i = 0; i < response.length; i++) {
      if (processedContent.includes(imageList[i])) {
        const cid = `cid:${response[i].cid}`
        processedContent = processedContent.replace(imageList[i], cid)
      }
    }

    return {
      content: processedContent,
      convertImageList: response
    }

  } catch (error) {
    console.error(`Base64 to CID conversion error: ${error.message}`)
    return { content, convertImageList: '' }
  }
}

// edit resize img style
export const addResponsiveImageStyles = (content) => {
  if (!content) return content

  const dom = document.createElement('div')
  dom.innerHTML = content
  const resizeDom = dom.querySelectorAll('figure img')

  if (resizeDom.length) {
    for (let i = 0; i < resizeDom.length; i++) {
      const img = resizeDom[i]
      img.removeAttribute('width')
      img.removeAttribute('height')

      img.setAttribute('width', '100%')
      img.setAttribute('height', '100%')

    }
  }

  return dom.innerHTML

}


