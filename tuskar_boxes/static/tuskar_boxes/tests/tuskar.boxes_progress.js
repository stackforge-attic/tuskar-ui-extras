
horizon.addInitFunction(function () {
  "use strict";

  module("Tuskar boxes progress (tuskar.boxes_progress.js)");

  test("update_progress", function () {
    var data = {
      "nodes": [{
        "uuid": "I'm sorry, Dave.",
        "cpu_arch": "HAL 9000",
        "role_slug": "exterminate",
        "state_slug": "smug",
        "node_title": "I'm afraid I can't do that.",
        "cpus": 1,
        "memory_mb": 0,
        "local_gb": 1000,
        "state_icon": "fa-circle-o"
      }]
    };

    tuskar.boxes_progress.update_progress(data);

    // No logic to test here, just make sure the function runs without errors.
    expect(0);
  });
});
