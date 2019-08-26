module decouple
   #(
	   parameter DEPTH = 2,
     parameter DIN = 16
	   )
   (
    input logic clk,
    input       rst,
    dti.consumer din,
    dti.producer dout
    );

    if (DEPTH == -1) begin
       logic [DIN : 0] memory [0 : 1]; //one bit for valid

       logic           empty;
       logic           full;
       logic           active;
       logic           handshake;

       assign active = memory[0][0];

       assign full = (active == 1) && (memory[1][0] == 1);
       assign empty = (active == 0);

       always_ff @(posedge clk) begin
          if(rst) begin
             for (int i = 0; i < 2; i++) begin
                memory[i] <= '0;
             end
          end else begin

             if (din.valid && !full) begin
                memory[active][DIN:1] <= din.data;
             end

             if (din.valid && !full) begin
                memory[active][0] <= 1'b1;
             end else if (dout.ready) begin
                memory[active][0] <= 1'b0;
             end
          end
       end

       assign dout.data = memory[active][DIN:1];
       assign dout.valid = ~empty;

       assign din.ready = ~full;

    end else if (DEPTH > 1) begin

      localparam MSB = $clog2(DEPTH);
      localparam W_DATA = DIN;
      logic [MSB:0] w_ptr;
      logic [MSB:0] r_ptr;
       logic [MSB:0] w_ptr_next;
       logic [MSB:0] r_ptr_next;
      logic empty;
      logic full;

       (* ram_style = "block" *) logic [W_DATA : 0] memory [0 : DEPTH-1]; //one bit for valid
       logic [W_DATA : 0] dout_s;

      assign empty = (w_ptr == r_ptr);
      assign full = (w_ptr[MSB-1:0] == r_ptr[MSB-1:0]) & (w_ptr[MSB]!=r_ptr[MSB]);
       always_ff @(posedge clk) begin
          if(rst) begin
             w_ptr <= 0;
          end else if(din.valid & ~full) begin
             w_ptr <= w_ptr + 1;
          end
       end

        always_ff @(posedge clk) begin
            if(rst) begin
              r_ptr <= 0;
           end else if(dout.ready & ~empty) begin
              r_ptr <= r_ptr_next;
            end
        end

        assign r_ptr_next = r_ptr + 1;

      always_ff @(posedge clk) begin
        if(din.valid & ~full) begin
          memory[w_ptr[MSB-1:0]] <= {din.data, din.valid};
        end
        dout_s <= memory[r_ptr_next[MSB-1:0]];
      end

      assign dout.data = dout_s[W_DATA:1];
      assign dout.valid = dout_s[0] & ~empty;

      assign din.ready = ~full;

   end else begin

      logic [DIN-1 : 0] din_reg_data;
      logic                         din_reg_valid;
      logic                         reg_empty;
      logic                         reg_ready;

      assign reg_ready = reg_empty;
      assign reg_empty = !din_reg_valid;

      always_ff @(posedge clk) begin
         if(rst | (!reg_empty && dout.ready)) begin
            din_reg_valid <= '0;
         end else if (reg_ready)begin
            din_reg_valid <= din.valid;
            din_reg_data <= din.data;
         end
      end

      assign din.ready = reg_ready;
      assign dout.data = din_reg_data;
      assign dout.valid = din_reg_valid;
   end

endmodule : decouple
