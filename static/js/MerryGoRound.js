/*
--- 
provides: 
- MerryGoRound
license: MIT-style
requires: 
  core/1.2.3: 
  - Class.Extras
  - Element.Event
  - Element.Style
  - Element.Dimensions
  - Fx.Tween
  - String
  - Array
description: A fully-automated, flexible, customizable carousel class for Mootools.
authors: 
- 3n
...
*/

var MerryGoRound = new Class({
  Implements: [Events, Options],
  options: {
    selector       : '*',
    cycle          : false,
    per_page       : 'auto',
    page_controls  : false,
    
    fx_options: {
      'property' : 'margin-left',
      'link'     : 'cancel'
    },
    
    // wrapper_width : 100,
    // wrapper_height : 100,
    wrapper_tag     : 'div',
    wrapper_options : {
      'class'  : 'merry-go-round-wrapper',
      'styles' : {
        'position' : 'relative'
      }
    },
    
    button_event : 'click',
    previous_button_tag     : 'a',
    previous_button_options : {
/*       'html'  : 'prev', */
      'class' : 'merry-go-round-previous',
      'styles' : {
        'position' : 'absolute',
        'left'     : 0
      }
    },
    next_button_tag     : 'a',
    next_button_options : {
/*       'html'  : 'next', */
      'class' : 'merry-go-round-next',
      'styles' : {
        'position' : 'absolute',
        'right'    : 0
      }
    },
    
    current_page_class : 'merry-go-round-current-page',
    page_controls_tag : 'div',
    page_controls_options : {
      'class' : 'merry-go-round-pagination',
      'styles' : {
        'overflow' : 'auto'
      }
    }
  },
  
  initialize: function(elem, options){
    this.setOptions(options);
    
    this.inner_element = $(elem);
    var method = this.inner_element.getParent() ? 'wraps' : 'grab';
    this.element = new Element(this.options.wrapper_tag, this.options.wrapper_options)[method](this.inner_element);

    this.riders        = this.element.getFirst().getChildren(this.options.selector);
    this.current_index = 0;
    
    if (this.riders.length === 0) return;

    this.scroll = new Fx.Tween(this.inner_element, this.options.fx_options);

    this.setup_styles();
    this.setup_pages();    
    
    if (this.pages.length > 1){
      if (this.options.page_controls) this.setup_page_controls();
      this.inject_buttons();
      this.add_events();
      this.fireEvent('pageShown', [0, this]);          
    }

    return this;
  },
  
  setup_styles: function(){
    this.element.setStyles({
      'height' : this.options.wrapper_height || this.riders[0].getHeight(),
      'width'  : this.options.wrapper_width  || this.inner_element.getWidth()
    });
    
    var total_height = 0;
    this.riders.each(function(x){ 
      total_height += x.getWidth() + x.getStyle('margin-left').toInt() + x.getStyle('margin-right').toInt(); 
    });
    this.inner_element.setStyles({
      'width' : total_height,
      'overflow' : 'hidden'
    });
  },

  setup_pages: function(){
    this.pages = [];
    
    if (this.options.per_page == 'auto'){
      var right_edge = this.element.getWidth();

      this.pages.include(this.riders[0]);
      
      for (var i = 1, ii = this.riders.length; i < ii; i++){
        var rider_left  = this.riders[i].getPosition(this.inner_element).x;
        var rider_width = this.riders[i].getWidth() 
                          + this.riders[i].getStyle('margin-left').toInt() 
                          + this.riders[i].getStyle('margin-right').toInt();

        if ( (rider_left < right_edge && rider_left + rider_width > right_edge)
          || (i > 0 && rider_left >= right_edge && !this.riders[i-1].retrieve('merry-go-round-page')) ) {
          this.riders[i].store('merry-go-round-page', true);
          this.pages.include(this.riders[i]);
          right_edge = -this._calculate_scroll(this.riders[i]) + this.element.getWidth();  
        }
      }
    } else if (this.options.per_page === 1){
      this.pages = this.riders;
    } else {
      for (var i = 1, ii = this.riders.length; i < ii; i++){
        if (i % this.options.per_page === 0) this.pages.include(this.riders[i]);
      }
    } 
  },
  
  setup_page_controls: function(){
    this.page_controls = new Element(this.options.page_controls_tag, this.options.page_controls_options).adopt(
      this.pages.map(function(p,i){
        var tag = this.options.page_controls_tag.test('ul','i') ? 'li' : this.options.page_controls_tag;
        return new Element(tag, {
          'class'  : i === 0 ? this.options.current_page_class : '',
          'events' : {
            'click' : this.scroll_to_page.bind(this, i)
          } 
        });
      }, this)
    ).inject(this.element);
    
    var total_width = 0;
    this.page_controls.getChildren().each(function(x){
      total_width += x.getWidth() + x.getStyle('margin-left').toInt() + x.getStyle('margin-right').toInt(); 
    });
    this.page_controls.setStyle('width', total_width);
  },
  
  inject_buttons: function(){
    var buttons = [
      this.previous_button = new Element(this.options.previous_button_tag, this.options.previous_button_options),
      this.next_button     = new Element(this.options.next_button_tag,     this.options.next_button_options)
    ];
            
    this.element.adopt(buttons);        
    buttons.each(function(button){ button.setStyle('top', button.getParent().getHeight()/2 - button.getHeight()/2 ); });

    if (!this.options.cycle) this.previous_button.setStyle('display','none');
  },
  
  add_events: function(){
    this.previous_button.addEvent(this.options.button_event, this.previous.bind(this));
    this.next_button.addEvent(this.options.button_event, this.next.bind(this));
  },

  next: function(){  
    this.scroll_to_page(++this.current_index);
  },
  previous: function(){
    this.scroll_to_page(--this.current_index);
  },
  
  _hide_or_show_buttons: function(page_index){
    if (!this.options.cycle){
      if (page_index === 0)
        this.previous_button.setStyle('display','none');
      else  
        this.previous_button.setStyle('display','block');

      if (page_index + 1 === this.pages.length)
        this.next_button.setStyle('display','none');
      else
        this.next_button.setStyle('display','block');
    }
  },
  _update_page_controls: function(page_index){
    $(this.page_controls).getChildren()
      .removeClass(this.options.current_page_class)
      [page_index].addClass(this.options.current_page_class);
  },
  
  _calculate_scroll: function(elem){
    return - elem.getPosition(this.inner_element).x 
           + elem.getStyle('margin-left').toInt()
           + this.inner_element.getStyle('padding-left').toInt();
  },
  scroll_to_page: function(page_index){
    if (page_index < 0) page_index = this.pages.length + page_index;
    else page_index = page_index % this.pages.length;
    this.current_index = page_index;
    
    this.fireEvent('pageShown', [page_index, this]);      
    this._hide_or_show_buttons(page_index); 
    if (this.options.page_controls) this._update_page_controls(page_index);

    this.scroll.start(this._calculate_scroll(this.pages[page_index]));
  }
  
});