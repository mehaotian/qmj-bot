const btnDom = d3.selectAll('.btn')

btnDom.on('click', function (e) {
    const parent = d3.select(this.parentNode);
    console.log(parent.selectAll('.img'))
    parent.selectAll('.img').each(function () {
        const element = d3.select(this);
        if (element.classed('none')) {
            element.classed('none', false);
        } else {
            element.classed('none', true);
        }
    });
})