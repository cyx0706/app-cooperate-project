
var PI = Math.PI;
let mouseMove = false;
var borderX = 0;
var clickX = 0;
var offX = 0;
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
    ctx.lineWidth = 1.5;
    ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.5)';
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

function createSlider(container){
    var sliderContainer = document.createElement('div');
    sliderContainer.className = 'sliderContainer';
    container.appendChild(sliderContainer);
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
    borderX = sliderContainer.offsetLeft;

    slider.addEventListener('mousedown', dragSlider);
    document.addEventListener('mouseup', checkSlider);
    document.addEventListener('mousemove',moveSlider);

}


function dragSlider(event){
    clickX = event.pageX - borderX*2;
    console.log("clickX:", clickX);
    mouseMove = true;
}

function moveSlider(event) {
    if(mouseMove){
        $('.sliderContainer').addClass('sliderContainer_active');
        var originX = event.pageX ;
        var toX =  originX - borderX * 2 - clickX;
        if (toX < 0){
            toX = 0;
        }
        if (toX > 300-40){
            toX = 300-40;
        }
        $('.slider').css('left', toX);
        $('.sliderMask').css('width', toX);
        $('#blockCanvas').css('left', -70+toX);
        $('#shadowCanvas').css('left', -70+toX);
    }
}

function giveTips(tip, status){
    tips = $('#tips');
    if(status){
        tips.children('.text').text("滑动位置正确");
        tips.children('.colorText').text(tip).css({"color": 'green'});
    }
    else{
        tips.children('.text').text("滑动位置错误");
        tips.children('.colorText').text(tip).css({'color': 'red'});
    }
    tips.animate({bottom: 0}, 100);
}

function hideTips() {
    tips.animate({bottom: -20}, 100);
}

function checkSlider() {
    if (mouseMove)
         mouseMove = false;
    var left = $('#blockCanvas').offset().left;
    if (Math.abs(left-offX-170) < 5){
        console.log('success!');
        $('.sliderContainer').removeClass('sliderContainer_active');
        $('.sliderContainer').addClass('sliderContainer_success');
        var success_tip = "成功";
        $('.colorText').addClass('success');
        giveTips(success_tip, 1)
    }
    else {
        console.log('false!');
        $('.sliderContainer').removeClass('sliderContainer_active');
        $('.sliderContainer').addClass('sliderContainer_fail');
        // setTimeout(function () {
        $('.coloredText').addClass('fail');
        var fail_tip = "失败";
        giveTips(fail_tip, 0);
        // },2);

        // $('.sliderContainer').removeClass('sliderContainer_fail');
        // $('.sliderContainer').addClass('sliderContainer_active');
        setTimeout(function () {
            $('#blockCanvas').animate({left: -70}, 1000);
            $('#shadowCanvas').animate({left: -70}, 1000);
            $('.sliderMask').animate({width: 0}, 1000);
            $('.slider').animate({left: 0}, 1000);
            $('.sliderContainer').removeClass('sliderContainer_fail');
            $('.colorText').removeClass('fail');
            hideTips();
        }, 2000);



    }

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
    captcha = document.getElementById('sliderCaptcha');
    var captchaPic = document.createElement('div');
    captchaPic.id = 'captchaPic';
    var tips = document.createElement('p');
    tips.id = "tips";
    var imgWrapper = document.createElement('div');
    imgWrapper.className = 'imgWrapper';
    var restart = document.createElement('i');
    var colored_text = document.createElement('span');
    colored_text.innerHTML="33333";
    colored_text.className = 'colorText';
    var text = document.createElement('span');
    text.innerHTML="33333";
    text.className = 'text';
    tips.appendChild(restart);
    tips.appendChild(colored_text);
    tips.appendChild(text);
    var pic_canvas = document.createElement('canvas');
    pic_canvas.id = 'picCanvas';
    var block_canvas = document.createElement('canvas');
    block_canvas.id = 'blockCanvas';
    var L = l + r * 2 + 3; // 滑块实际边长
    var shadow_canvas = document.createElement('canvas');
    var bkColor = document.createElement('div');
    bkColor.className = 'bkColor';
    shadow_canvas.id = 'shadowCanvas';
    imgWrapper.appendChild(pic_canvas);
    imgWrapper.appendChild(tips);
    captcha.appendChild(bkColor);
    bkColor.appendChild(captchaPic);
    captchaPic.appendChild(imgWrapper);
    captchaPic.appendChild(shadow_canvas);
    captchaPic.appendChild(block_canvas);
    var context = pic_canvas.getContext('2d');
    var context3 = shadow_canvas.getContext('2d');
    var context2 = block_canvas.getContext('2d');
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
    sha(context3,170, 50, r,L,'clip', 'destination-over');
    offX = $('#blockCanvas').offset().left;
    createSlider(captcha);


});

// var slider = $('slider');
//     slider.on({
//         'mousedown': function () {
//             console.log("mousedown!");
//             dragSlider();
//         },
//         'mouseup' :function () {
//             console.log("mouseup!");
//             checkSlider();
// }
// });





