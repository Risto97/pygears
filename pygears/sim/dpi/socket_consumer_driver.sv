`ifndef SOCKET_CONSUMER_DRIVER_SV
 `define SOCKET_CONSUMER_DRIVER_SV

class socket_consumer_driver#(type DATA_T = bit [15:0]);

   virtual dti_verif_if#(DATA_T) vif;
   string  name;

	 chandle handle;

   function new
     (
      virtual dti_verif_if#(DATA_T) vif,
      string  name = "socket_consumer_driver",
      int     port = 1234
      );
      this.vif = vif;
      this.name = name;
	    handle = sock_open($sformatf("tcp://localhost:%d", port), name);
   endfunction

   task init();
      vif.ready <= 1'b0;
      @(negedge vif.rst);
   endtask

   task main();
      init();
      get_and_drive();
	    sock_close(handle);
   endtask

   task get_and_drive();
      int ret;
      bit[$bits(DATA_T)-1 : 0] data;

      forever begin

         do begin
            @(posedge vif.clk);
            #1;
         end while(!vif.valid);

         data = vif.data;
         ret = sock_put(handle, data);
         `verif_info($sformatf("Consumer driver %s sent: %p with ret %0d at %0t", name, DATA_T'(data), ret, $time), 2);
         if (ret == 1) return;

         do begin
            @(negedge vif.clk);
            vif.ready <= 1'b0;
	          ret = sock_get(handle, data);
            if (ret == 1) return;
         end while (ret == 2);
         `verif_info($sformatf("Consumer driver %s got ret %0d at %0t", name, ret, $time), 2);

         vif.ready <= 1'b1;
      end

   endtask

endclass

`endif
