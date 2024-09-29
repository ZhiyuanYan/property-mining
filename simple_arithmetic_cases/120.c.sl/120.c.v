module top (
    input wire selector,
    input wire clk,
    input wire rst,
    output reg [9:0] sn,
    output reg [9:0] i
);
    
    always @(posedge clk) begin
        if(rst)begin 
            sn <= 0;
            i <= 1;
        end else begin
            if((selector&&(i<=250)))begin
                i<= i + 1;
                sn <= sn + 1;
            end
            else begin
                i<=i;
                sn<=sn;
            end
        
        end
        
    end
    assert property (!((i>250)&&(sn!=250)&&(sn!=0)));
endmodule