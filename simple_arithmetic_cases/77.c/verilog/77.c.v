module top (
    input wire selector,
    input wire clk,
    input wire rst,
    output reg [14:0] i,
    output reg [14:0] y,
    output reg [14:0] x
);

    always@(posedge clk) begin
        $display("i: %b, y: %b, x: %b", i, y, x);
    end 

    
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
    // assert property (!((i<y)&(i>=x)));
endmodule