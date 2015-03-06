tuskar.boxes = (function () {
  'use strict';

  var module = {};


  module.get_role_counts = function ($flavor) {
    var roles = {};
    $flavor.find('div.boxes-drop-roles div.boxes-role').each(function () {
      var $this = $(this);
      var name = $this.data('name');
      var count = +$this.find('input.number-picker').val();
      roles[name] = count;
    });
    return roles;
  };

  module.update_maximums = function ($flavor, roles, nodes) {
    var used = 0;
    $.each(roles, function (key, value) { used += value; });
    $flavor.find('div.boxes-drop-roles div.boxes-role').each(function () {
      var $this = $(this);
      var role = $this.data('name');
      var $picker = $this.find('input.number-picker');
      $picker.attr('max', Math.max(0, nodes - used + roles[role]));
    });
  };

  module.update_nodes = function ($flavor, roles) {
    var role_names = Object.getOwnPropertyNames(roles);
    var count = 0;
    var role = 0;
    $flavor.find('div.boxes-nodes div.boxes-node').each(function () {
      var $this = $(this);
      $this.removeClass('boxes-role-controller boxes-role-compute boxes-role-cinder-storage boxes-role-swift-storage boxes-role-none');
      while (count >= roles[role_names[role]]) {
        role += 1;
        count = 0;
      }
      if (!role_names[role]) {
        $(this).html('free');
        $(this).addClass('boxes-role-none');
      } else {
        $this.addClass('boxes-role-' + role_names[role]).html('&nbsp;');
      }
      count += 1;
    });
    var free_nodes = $flavor.find('div.boxes-nodes div.boxes-role-none').length;
    $flavor.find('span.free-nodes').text(free_nodes);
  };

  module.update_boxes = function () {
    $('div.boxes-flavor').each(function () {
        var $flavor = $(this);
        var role_counts = module.get_role_counts($flavor);
        var nodes_count = $flavor.find('div.boxes-nodes div.boxes-node').length;
        module.update_nodes($flavor, role_counts);
        module.update_maximums($flavor, role_counts, nodes_count);
    });
  };

  module.init = function () {
    if ($('div.boxes-available-roles').length === 0) {
      // Only activate on a page that has the right classes.
      return;
    }
    $('div.boxes-role:not(.boxes-role-invalid)').draggable({
        revert: 'invalid',
        helper: 'clone',
        zIndex: 1000,
        opacity: 0.5
    });
    $('div.boxes-drop').droppable({
        accept: 'div.boxes-role',
        activeClass: 'boxes-drop-active',
        hoverClass: 'boxes-drop-hover',
        tolerance: 'touch',
        drop: function (ev, ui) {
          ui.draggable.appendTo($(this).parent().prev('.boxes-drop-roles'));
          var $count = ui.draggable.find('input.number-picker');
          if (+$count.val() < 1 && +$count.attr('max') >= 1) { $count.val(1); }
          ui.draggable.find('input.boxes-flavor'
              ).val($(this).closest('.boxes-flavor').data('flavor'));
          $count.trigger('change');
          window.setTimeout(module.update_boxes, 0);
        }
    });
    $('div.boxes-available-roles').droppable({
        accept: 'div.boxes-role',
        activeClass: 'boxes-drop-active',
        hoverClass: 'boxes-drop-hover',
        tolerance: 'touch',
        drop: function (ev, ui) {
          ui.draggable.appendTo(this);
          ui.draggable.find('input.boxes-flavor').val('');
          ui.draggable.find('input.number-picker').trigger('change').val(0);
          window.setTimeout(module.update_boxes, 0);
        }
    });

    module.update_boxes();
    $('input.number-picker').change(module.update_boxes);

    $('.boxes-roles-menu li a').click(function () {
        var name = $(this).data('role');
        var $drop = $(this).closest('.boxes-drop-group').prev('.boxes-drop-roles');
        var $role = $('.boxes-role[data-name="' + name + '"]');
        var $count = $role.find('input.number-picker');
        var $flavor = $role.find('input.boxes-flavor');
        $role.appendTo($drop);
        if (+$count.val() < 1) { $count.val(1); }
        $flavor.val($drop.closest('.boxes-flavor').data('flavor'));
        $count.trigger('change');
        window.setTimeout(module.update_boxes, 0);
    });

    $('.deploy-role-remove').click(function () {
        var $role = $(this).closest('.boxes-role');
        var $count = $role.find('input.number-picker');
        var $flavor = $role.find('input.boxes-flavor');
        var $drop = $('.boxes-available-roles');
        $role.appendTo($drop);
        $flavor.val('');
        $count.val(0);
        $count.trigger('change');
        window.setTimeout(module.update_boxes, 0);
    });
  };

  horizon.addInitFunction(module.init);
  return module;
} ());
