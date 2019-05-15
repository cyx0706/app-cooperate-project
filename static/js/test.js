var canvas = document.getElementById('canvas');
var block = document.getElementById('block');
var canvas_ctx = canvas.getContext('2d');
var block_ctx = block.getContext('2d');
var img = document.createElement('img');
img.onload = function() {
    canvas_ctx.drawImage(img, 0, 0, 310, 155);
    block_ctx.drawImage(img, 0, 0, 310, 155);
};
img.src = '/media/avatar_default';


var x = 150, y = 40, w = 42, r = 10, PI = Math.PI ;
  function draw(ctx) {
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x + w, y);
    ctx.lineTo(x + w, y + w);
    ctx.lineTo(x, y + w);
    ctx.clip()
  }
  draw(canvas_ctx);
  draw(block_ctx);


img.onload = function() {
    ctx.drawImage(img, 0, 0, 310, 155);
    block_ctx.drawImage(img, 0, 0, 310, 155);
    var blockWidth = w + r * 2;
  var _y = y - r * 2 + 2; // 滑块实际的y坐标
  var ImageData = block_ctx.getImageData(x, _y, blockWidth, blockWidth);
  block.width = blockWidth
+   block_ctx.putImageData(ImageData, 0, _y)
  };