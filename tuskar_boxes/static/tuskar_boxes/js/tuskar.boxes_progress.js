tuskar.boxes_progress = function () {
  'use static';
  var module = {};

  module.init = function () {
    module.nodes_template = Hogan.compile($('#nodes-template').html() || '');
  };

  module.update_progress = function (data) {
    var $nodes = $('div.boxes-nodes');
    $nodes.html(module.nodes_template.render(data));
    $nodes.find('div.boxes-node').popover({
      'trigger': 'hover',
      'placement': 'auto',
      'delay': 500,
      'html': true
    });
  };

  // Attach to the original update procedure.
  var orig_update_progress = tuskar.deployment_progress.update_progress;
  tuskar.deployment_progress.update_progress = function () {
    orig_update_progress.apply(tuskar.deployment_progress, arguments);
    module.update_progress.apply(module, arguments);
  };

  horizon.addInitFunction(module.init);
  return module;
} ();
