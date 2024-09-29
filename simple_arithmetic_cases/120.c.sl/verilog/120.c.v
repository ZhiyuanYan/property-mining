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
            if((selector&&(i<=200)))begin
                i<= i + 1;
                sn <= sn + 1;
            end
            else begin
                i<=i;
                sn<=sn;
            end
        
        end
        
    end
    // assert property (!((i>200)&&(sn!=200)&&(sn!=0)));
endmodule