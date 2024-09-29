module top (
    input wire selector,
    input wire clk,
    input wire rst,

);


    reg [30:0] i;
    reg [30:0] y;
    reg [30:0] x;
    
    always @(posedge clk) begin
        if(rst)begin
            x <= 500;
            y<=450;
            i<=0;
        end
        else begin
            if(selector)begin
                if((i < y))begin
                    i <= i + 1;
                    y<=y;
                    x<=x;
                end
                else begin
                    i <= i;
                    y <= y;
                    x<=x;
                end
            end
        end
    end
    assert property ((!((i<y)&(i>=x))));
endmodule