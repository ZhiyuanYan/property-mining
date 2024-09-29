module top (
    input wire selector,
    input wire clk,
    input wire rst,
    output reg [9:0] sn,
    output reg [9:0] i
);

    always@(posedge clk) begin
        $display("sn: %b, i: %b", sn, i);
    end 
    
    always @(posedge clk) begin
        if(rst)begin
            sn <= 0;
            i <= 1;
        end else begin
            if(selector&&(i<=300))begin
                i<= i + 1;
                sn <= sn + 1;
                // n<=n;
            end
            else begin
                sn<=sn;
                i<=i;
                // n<=n;
            end
        
        end
        
    end
    // assert property (!((i>50)&&(sn!=50)&&(sn!=0)));
endmodule