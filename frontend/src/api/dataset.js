import request from "../utils/request";

/**
 * 上传并转化数据集
 * @param {File} file - ZIP 压缩包
 * @param {string} format - 输入格式 (voc / coco / csv)
 * @param {string} classes - 类别列表（可选）
 * @returns {Promise}
 */
export function convertDataset(file, format, classes = "") {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("format", format);
  if (classes) {
    formData.append("classes", classes);
  }

  return request({
    url: "/dataset/convert",
    method: "post",
    data: formData,
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
}

/**
 * 下载转化后的数据集
 * @param {number} userId - 用户 ID
 * @returns {Promise}
 */
export function downloadConvertedDataset(userId) {
  return request({
    url: `/dataset/download/${userId}`,
    method: "get",
    responseType: "blob",
  });
}
