module top (
    input wire selector,
    input wire clk,
    input wire rst,
    output reg [7:0] sn,
    output reg [7:0] i
);


    always@(posedge clk) begin
        $display("sn: %b, i: %b", sn, i);
    end 

    always @(posedge clk) begin
        if(rst)begin
            sn <= 0;
            i <= 1;
        end else begin
            if(selector&&(i<=70))begin
                i<= i + 1;
                sn <= sn + 1;
            end
            else begin
                sn<=sn;
                i<=i;
            end
        
        end
        
    end
    // assert property (!((i>70)&&(sn!=70)&&(sn!=0)));
endmodule