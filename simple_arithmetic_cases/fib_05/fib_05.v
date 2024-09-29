module top (
    input wire selector,
    input wire clk,
    input wire rst,
    // output reg [10:0] y,
    // output reg [10:0] x,
    // output reg [10:0] j,
    // output reg [10:0] i
);

    reg [15:0] y;
    reg [15:0] x;
    reg [15:0] j;
    reg [15:0] i;
    
    always @(posedge clk) begin
        if(rst)begin
            y<=0;
            x<=0;
            j<=0;
            i<=0;
        end
        else begin
            if(selector&&(j<300))begin
                x <= x+1;
                y <= y+1;
                i <= i+x+ 1;
                j <= j+y+1;
            end
            else if(!selector&&(j<300)) begin
                x <= x+1;
                y <= y+1;
                i <= i+x+ 1;
                j <= j+y+2;
            end
            else begin
                x <= x;
                y <= y;
                i <= i;
                j <= j;
            end
        end
    end
    assert property ((j>=i));
endmodule