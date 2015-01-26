horizon.addInitFunction(function () {
  "use strict";

  module("Tuskar boxes (tuskar.boxes.js)");

  test("get_role_counts", function () {
    var $flavor = $($('div.boxes-flavor')[0]);
    var role_counts = tuskar.boxes.get_role_counts($flavor);

    deepEqual(role_counts, {
      "cinder-storage": 0,
      "compute": 1,
      "controller": 1,
      "swift-storage": 0
    });
  });

  test("update_maximums", function () {
    var $flavor = $($('div.boxes-flavor')[0]);
    var role_counts = {
      "cinder-storage": 0,
      "compute": 2,
      "controller": 1,
      "swift-storage": 0
    };

    tuskar.boxes.update_maximums($flavor, role_counts, 4);
    equal($('div.boxes-role-cinder-storage input.number-picker').attr('max'), 1);
    equal($('div.boxes-role-compute input.number-picker').attr('max'), 3);
    equal($('div.boxes-role-controller input.number-picker').attr('max'), 2);
    equal($('div.boxes-role-swift-storage input.number-picker').attr('max'), 1);
    tuskar.boxes.update_maximums($flavor, role_counts, 2);
    equal($('div.boxes-role-cinder-storage input.number-picker').attr('max'), 0);
    equal($('div.boxes-role-compute input.number-picker').attr('max'), 1);
    equal($('div.boxes-role-controller input.number-picker').attr('max'), 0);
    equal($('div.boxes-role-swift-storage input.number-picker').attr('max'), 0);
  });

  test("update_nodes", function() {
    var $flavor = $($('div.boxes-flavor')[0]);
    var role_counts = {
      "cinder-storage": 0,
      "compute": 2,
      "controller": 1,
      "swift-storage": 0
    };

    equal($('div.boxes-nodes div.boxes-role-').length, 2);
    equal($('div.boxes-nodes div.boxes-role-cinder-storage').length, 0);
    equal($('div.boxes-nodes div.boxes-role-compute').length, 1);
    equal($('div.boxes-nodes div.boxes-role-controller').length, 1);
    equal($('div.boxes-nodes div.boxes-role-swift-storage').length, 0);
    tuskar.boxes.update_nodes($flavor, role_counts);
    equal($('div.boxes-nodes div.boxes-role-none').length, 1);
    equal($('div.boxes-nodes div.boxes-role-cinder-storage').length, 0);
    equal($('div.boxes-nodes div.boxes-role-compute').length, 2);
    equal($('div.boxes-nodes div.boxes-role-controller').length, 1);
    equal($('div.boxes-nodes div.boxes-role-swift-storage').length, 0);
  });
});
