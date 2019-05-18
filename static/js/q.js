
var PI = Math.PI;

function draw(ctx, x, y, r, l, operation, option) {
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.arc(x + l / 2, y - r + 2, r, 0.72 * PI, 2.26 * PI);
    ctx.lineTo(x + l, y);
    ctx.arc(x + l + r - 2, y + l / 2, r, 1.21 * PI, 2.78 * PI);
    ctx.lineTo(x + l, y + l);
    ctx.lineTo(x, y + l);
    ctx.arc(x + r - 2, y + l / 2, r + 0.4, 2.76 * PI, 1.24 * PI, true);
    ctx.lineTo(x, y);
    ctx.lineWidth = 1;
    ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.2)';
    ctx.closePath();
    ctx.stroke();
    ctx[operation]();

    ctx.globalCompositeOperation = option;
}

function sha(ctx, x, y, r, l, operation, option) {
    ctx.shadowColor= "rgb(0, 0, 0, 1)";
    ctx.shadowBlur = 10;
    ctx.shadowOffsetX = 5;
    ctx.shadowOffsetY = 5;
    draw(ctx, x, y, r, l, operation, option);
    ctx.fill();
}
function createSlider(){
    var sliderContainer = document.createElement('div');
    sliderContainer.className = 'sliderContainer';
    document.body.appendChild(sliderContainer);
    var sliderMask = document.createElement('div');
    sliderContainer.appendChild(sliderMask);
    sliderMask.className = 'sliderMask';
    sliderMask.style = 'width: 0px;';
    var slider = document.createElement('div');
    sliderMask.appendChild(slider);
    slider.className = 'slider';
    slider.style = "left: 0px";
    var sliderIcon = document.createElement('span');
    sliderIcon.className = 'sliderIcon';
    slider.appendChild(sliderIcon);
    var sliderText = document.createElement('span');
    sliderText.className = 'sliderText';
    sliderText.innerHTML = "向右滑动填充拼图";
    sliderContainer.appendChild(sliderText);
}

$(function () {
    var l = 20;
      // 滑块边长
        r = 9;
      // 滑块半径
  w = 260;
      // canvas宽度
  h = 116;
      // canvas高度
  var L = l + r * 2 + 3; // 滑块实际边长
    var canvas = document.getElementById('test');
    var context = canvas.getContext('2d');
    var canvas2 = document.getElementById('test2');
    var canvas3 = document.getElementById('test3');
    var context3 = canvas3.getContext('2d');
    var context2 = canvas2.getContext('2d');
    img = new Image();
    img.onload = function () {
        context.drawImage(img, 0 ,0, 300, 150);
    };
    img.src = "/media/777.jpg";
    height = img.height;
    width = img.width;
    img = new Image();
    img.onload = function () {
        context2.drawImage(img, 0 ,0, 300, 150, );
    };
    img.src = "/media/777.jpg";
    height = img.height;
    width = img.width;
    draw(context2,170, 50, r,L,'clip', 'destination-over');
    // shadowPuzzle(context3, 120, 100, 170, 150)
    draw(context, 170, 50, r,L,'fill', 'overlay');
    sha(context3,170, 50, r,L,'clip', 'destination-over')
    createSlider();
});


