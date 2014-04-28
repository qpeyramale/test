openerp.sudokeys_simpac = function(instance){

    var _t = instance.web._t,
    _lt = instance.web._lt;
    var QWeb = instance.web.qweb;
    
    instance.web.form.FieldMany2One = instance.web.form.FieldMany2One.extend({
        init: function(field_manager, node) {
            this._super(field_manager, node);
            var self=this;
            self.limit = 25;
        },
    });
    
}
