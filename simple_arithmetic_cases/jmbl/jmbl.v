module top (
    input wire selector,
    input wire clk,
    input wire rst,
    output reg [18:0] x,
    output reg [18:0] y
);



    
    always @(posedge clk) begin
        if(rst)begin
            x<=1;
            y<=0;
        end
        else begin
                if (y<200) begin
                    x<=x+y;
                    y<=y+1;
                end
                else begin
                    x<=x;
                    y<=y;
                end
            end
        end
    
    assert property ((y<200)||(x>=y));
endmodule