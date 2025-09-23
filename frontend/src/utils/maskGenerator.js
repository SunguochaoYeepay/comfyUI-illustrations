/**
 * 遮罩生成器工具类
 * 用于将用户的选择区域转换为黑白遮罩图像
 */
export default class MaskGenerator {
  constructor() {
    this.canvas = document.createElement('canvas')
    this.ctx = this.canvas.getContext('2d')
  }

  /**
   * 从Fabric.js选择对象生成遮罩
   * @param {Object} selection - Fabric.js选择对象
   * @param {number} imageWidth - 图像宽度
   * @param {number} imageHeight - 图像高度
   * @returns {Promise<Blob>} 遮罩图像Blob
   */
  async generateMaskFromSelection(selection, imageWidth, imageHeight) {
    // 设置画布大小
    this.canvas.width = imageWidth
    this.canvas.height = imageHeight
    
    // 清空画布
    this.ctx.clearRect(0, 0, imageWidth, imageHeight)
    
    // 根据选择对象类型生成遮罩
    if (selection.type === 'rect') {
      return this.generateRectMask(selection, imageWidth, imageHeight)
    } else if (selection.type === 'path') {
      return this.generatePathMask(selection, imageWidth, imageHeight)
    } else if (selection.type === 'polygon') {
      return this.generatePolygonMask(selection, imageWidth, imageHeight)
    } else {
      throw new Error('不支持的选择对象类型: ' + selection.type)
    }
  }

  /**
   * 生成矩形遮罩
   * @param {Object} rect - 矩形对象
   * @param {number} imageWidth - 图像宽度
   * @param {number} imageHeight - 图像高度
   * @returns {Promise<Blob>} 遮罩图像Blob
   */
  async generateRectMask(rect, imageWidth, imageHeight) {
    // 设置画布大小
    this.canvas.width = imageWidth
    this.canvas.height = imageHeight
    
    // 清空画布
    this.ctx.clearRect(0, 0, imageWidth, imageHeight)
    
    // 绘制白色矩形（选择区域）
    this.ctx.fillStyle = 'white'
    this.ctx.fillRect(
      rect.left,
      rect.top,
      rect.width,
      rect.height
    )
    
    return this.canvasToBlob()
  }

  /**
   * 生成路径遮罩（画笔轨迹）
   * @param {Object} path - 路径对象
   * @param {number} imageWidth - 图像宽度
   * @param {number} imageHeight - 图像高度
   * @returns {Promise<Blob>} 遮罩图像Blob
   */
  async generatePathMask(path, imageWidth, imageHeight) {
    // 设置画布大小
    this.canvas.width = imageWidth
    this.canvas.height = imageHeight
    
    // 清空画布
    this.ctx.clearRect(0, 0, imageWidth, imageHeight)
    
    // 设置绘制样式
    this.ctx.fillStyle = 'white'
    this.ctx.strokeStyle = 'white'
    this.ctx.lineWidth = path.strokeWidth || 10
    this.ctx.lineCap = 'round'
    this.ctx.lineJoin = 'round'
    
    // 绘制路径
    this.ctx.beginPath()
    
    // 解析路径数据
    const pathData = path.path
    if (Array.isArray(pathData)) {
      this.drawPathFromCommands(pathData)
    } else if (typeof pathData === 'string') {
      this.drawPathFromString(pathData)
    }
    
    this.ctx.stroke()
    
    return this.canvasToBlob()
  }

  /**
   * 生成多边形遮罩
   * @param {Object} polygon - 多边形对象
   * @param {number} imageWidth - 图像宽度
   * @param {number} imageHeight - 图像高度
   * @returns {Promise<Blob>} 遮罩图像Blob
   */
  async generatePolygonMask(polygon, imageWidth, imageHeight) {
    // 设置画布大小
    this.canvas.width = imageWidth
    this.canvas.height = imageHeight
    
    // 清空画布
    this.ctx.clearRect(0, 0, imageWidth, imageHeight)
    
    // 设置绘制样式
    this.ctx.fillStyle = 'white'
    
    // 绘制多边形
    this.ctx.beginPath()
    
    if (polygon.points && Array.isArray(polygon.points)) {
      // 从点数组绘制
      this.ctx.moveTo(polygon.points[0].x, polygon.points[0].y)
      for (let i = 1; i < polygon.points.length; i++) {
        this.ctx.lineTo(polygon.points[i].x, polygon.points[i].y)
      }
    } else if (polygon.path && typeof polygon.path === 'string') {
      // 从路径字符串绘制
      this.drawPathFromString(polygon.path)
    }
    
    this.ctx.closePath()
    this.ctx.fill()
    
    return this.canvasToBlob()
  }

  /**
   * 从路径命令数组绘制路径
   * @param {Array} commands - 路径命令数组
   */
  drawPathFromCommands(commands) {
    for (const command of commands) {
      switch (command[0]) {
        case 'M': // MoveTo
          this.ctx.moveTo(command[1], command[2])
          break
        case 'L': // LineTo
          this.ctx.lineTo(command[1], command[2])
          break
        case 'C': // CurveTo
          this.ctx.bezierCurveTo(command[1], command[2], command[3], command[4], command[5], command[6])
          break
        case 'Q': // QuadraticCurveTo
          this.ctx.quadraticCurveTo(command[1], command[2], command[3], command[4])
          break
        case 'Z': // ClosePath
          this.ctx.closePath()
          break
      }
    }
  }

  /**
   * 从路径字符串绘制路径
   * @param {string} pathString - SVG路径字符串
   */
  drawPathFromString(pathString) {
    // 简化的SVG路径解析
    const commands = pathString.match(/[MmLlHhVvCcSsQqTtAaZz][^MmLlHhVvCcSsQqTtAaZz]*/g) || []
    
    for (const command of commands) {
      const type = command[0]
      const coords = command.slice(1).trim().split(/[\s,]+/).map(Number).filter(n => !isNaN(n))
      
      switch (type) {
        case 'M':
        case 'm':
          if (coords.length >= 2) {
            this.ctx.moveTo(coords[0], coords[1])
          }
          break
        case 'L':
        case 'l':
          if (coords.length >= 2) {
            this.ctx.lineTo(coords[0], coords[1])
          }
          break
        case 'C':
        case 'c':
          if (coords.length >= 6) {
            this.ctx.bezierCurveTo(coords[0], coords[1], coords[2], coords[3], coords[4], coords[5])
          }
          break
        case 'Z':
        case 'z':
          this.ctx.closePath()
          break
      }
    }
  }

  /**
   * 从点数组生成遮罩
   * @param {Array} points - 点数组 [{x, y}, ...]
   * @param {number} imageWidth - 图像宽度
   * @param {number} imageHeight - 图像高度
   * @param {number} brushSize - 画笔大小
   * @returns {Promise<Blob>} 遮罩图像Blob
   */
  async generateMaskFromPoints(points, imageWidth, imageHeight, brushSize = 10) {
    // 设置画布大小
    this.canvas.width = imageWidth
    this.canvas.height = imageHeight
    
    // 清空画布
    this.ctx.clearRect(0, 0, imageWidth, imageHeight)
    
    // 设置绘制样式
    this.ctx.fillStyle = 'white'
    this.ctx.strokeStyle = 'white'
    this.ctx.lineWidth = brushSize
    this.ctx.lineCap = 'round'
    this.ctx.lineJoin = 'round'
    
    // 绘制点
    if (points.length === 1) {
      // 单个点，绘制圆形
      this.ctx.beginPath()
      this.ctx.arc(points[0].x, points[0].y, brushSize / 2, 0, Math.PI * 2)
      this.ctx.fill()
    } else if (points.length > 1) {
      // 多个点，绘制路径
      this.ctx.beginPath()
      this.ctx.moveTo(points[0].x, points[0].y)
      
      for (let i = 1; i < points.length; i++) {
        this.ctx.lineTo(points[i].x, points[i].y)
      }
      
      this.ctx.stroke()
    }
    
    return this.canvasToBlob()
  }

  /**
   * 应用羽化效果到遮罩
   * @param {Blob} maskBlob - 原始遮罩Blob
   * @param {number} featherRadius - 羽化半径
   * @returns {Promise<Blob>} 羽化后的遮罩Blob
   */
  async applyFeathering(maskBlob, featherRadius = 5) {
    return new Promise((resolve) => {
      const img = new Image()
      img.onload = () => {
        // 设置画布大小
        this.canvas.width = img.width
        this.canvas.height = img.height
        
        // 清空画布
        this.ctx.clearRect(0, 0, img.width, img.height)
        
        // 应用高斯模糊效果
        this.ctx.filter = `blur(${featherRadius}px)`
        this.ctx.drawImage(img, 0, 0)
        
        // 重置滤镜
        this.ctx.filter = 'none'
        
        resolve(this.canvasToBlob())
      }
      img.src = URL.createObjectURL(maskBlob)
    })
  }

  /**
   * 反转遮罩（黑白反转）
   * @param {Blob} maskBlob - 原始遮罩Blob
   * @returns {Promise<Blob>} 反转后的遮罩Blob
   */
  async invertMask(maskBlob) {
    return new Promise((resolve) => {
      const img = new Image()
      img.onload = () => {
        // 设置画布大小
        this.canvas.width = img.width
        this.canvas.height = img.height
        
        // 清空画布
        this.ctx.clearRect(0, 0, img.width, img.height)
        
        // 绘制图像
        this.ctx.drawImage(img, 0, 0)
        
        // 获取图像数据
        const imageData = this.ctx.getImageData(0, 0, img.width, img.height)
        const data = imageData.data
        
        // 反转像素值
        for (let i = 0; i < data.length; i += 4) {
          data[i] = 255 - data[i]     // R
          data[i + 1] = 255 - data[i + 1] // G
          data[i + 2] = 255 - data[i + 2] // B
          // Alpha通道保持不变
        }
        
        // 放回图像数据
        this.ctx.putImageData(imageData, 0, 0)
        
        resolve(this.canvasToBlob())
      }
      img.src = URL.createObjectURL(maskBlob)
    })
  }

  /**
   * 将画布转换为Blob
   * @returns {Promise<Blob>} 图像Blob
   */
  canvasToBlob() {
    return new Promise((resolve) => {
      this.canvas.toBlob((blob) => {
        resolve(blob)
      }, 'image/png')
    })
  }

  /**
   * 获取遮罩的预览URL
   * @param {Blob} maskBlob - 遮罩Blob
   * @returns {string} 预览URL
   */
  getMaskPreviewUrl(maskBlob) {
    return URL.createObjectURL(maskBlob)
  }

  /**
   * 释放预览URL
   * @param {string} url - 预览URL
   */
  revokeMaskPreviewUrl(url) {
    URL.revokeObjectURL(url)
  }
}
